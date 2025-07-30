import puppeteer, { Browser, Page } from 'puppeteer';
import { AcademicProfile, Collaborator, SearchResponse, CollaboratorsResponse, SearchParams, CollaboratorParams } from './types';
import * as fs from 'fs';
import * as path from 'path';

export class YokAkademikService {
  private browser: Browser | null = null;
  private baseUrl = 'https://akademik.yok.gov.tr/';
  private defaultPhotoUrl = '/default_photo.jpg';

  constructor() {}

  private async getBrowser(): Promise<Browser> {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: 'new',
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu'
        ]
      });
    }
    return this.browser;
  }

  private async createPage(): Promise<Page> {
    const browser = await this.getBrowser();
    const page = await browser.newPage();
    
    // Set user agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    
    // Set viewport
    await page.setViewport({ width: 1920, height: 1080 });
    
    return page;
  }

  private generateSessionId(): string {
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0];
    const uniqueId = Math.random().toString(36).substring(2, 10);
    return `session_${timestamp}_${uniqueId}`;
  }

  private sanitizeFilename(name: string): string {
    return name.replace(/[^A-Za-z0-9ĞÜŞİÖÇğüşiöç ]+/g, '_').trim().replace(/\s+/g, '_');
  }

  private parseLabelsAndKeywords(text: string): { green_label: string; blue_label: string; keywords: string } {
    const parts = text.split(';').map(p => p.trim());
    const left = parts[0] || '';
    const restKeywords = parts.slice(1).filter(p => p.trim());
    
    const leftParts = left.split(/\s{2,}|\t+/);
    const green_label = leftParts[0]?.trim() || '-';
    const blue_label = leftParts[1]?.trim() || '-';
    
    const keywords = [];
    if (leftParts.length > 2) {
      keywords.push(...leftParts.slice(2).filter(p => p.trim()));
    }
    keywords.push(...restKeywords);
    
    return {
      green_label,
      blue_label,
      keywords: keywords.length > 0 ? keywords.join(' ; ') : '-'
    };
  }

  public async searchAcademicProfiles(params: SearchParams): Promise<SearchResponse> {
    const page = await this.createPage();
    const sessionId = this.generateSessionId();
    const profiles: AcademicProfile[] = [];
    let profileIdCounter = 1;

    try {
      console.log(`[INFO] Searching for: ${params.name}`);
      
      // Navigate to search page
      await page.goto(`${this.baseUrl}AkademikArama/`);
      
      // Wait for search form and handle cookies
      await page.waitForSelector('#aramaTerim');
      
      try {
        const cookieButton = await page.waitForSelector('button:has-text("Tümünü Kabul Et")', { timeout: 5000 });
        if (cookieButton) {
          await cookieButton.click();
          console.log('[DEBUG] Cookies accepted');
        }
      } catch (e) {
        console.log('[DEBUG] Cookie button not found');
      }

      // Perform search
      await page.type('#aramaTerim', params.name);
      await page.click('#searchButton');
      
      // Switch to Academics tab
      await page.waitForSelector('a:has-text("Akademisyenler")');
      await page.click('a:has-text("Akademisyenler")');

      let pageNum = 1;
      const profileUrls = new Set<string>();

      while (true) {
        console.log(`[INFO] Loading page ${pageNum}...`);
        
        // Wait for profile rows
        await page.waitForSelector('tr[id^="authorInfo_"]', { timeout: 10000 });
        
        const profileRows = await page.$$('tr[id^="authorInfo_"]');
        console.log(`[INFO] Found ${profileRows.length} profiles on page ${pageNum}`);

        if (profileRows.length === 0) {
          console.log('[INFO] No profiles found, ending loop');
          break;
        }

        for (const row of profileRows) {
          try {
            const infoTd = await row.$('td h6');
            if (!infoTd) continue;

            // Get labels
            const labelLinks = await infoTd.$$('a.anahtarKelime');
            const green_label = labelLinks[0] ? await labelLinks[0].evaluate(el => el.textContent?.trim() || '') : '';
            const blue_label = labelLinks[1] ? await labelLinks[1].evaluate(el => el.textContent?.trim() || '') : '';

            // Apply filters if specified
            if (params.field_id && green_label !== this.getFieldNameById(params.field_id)) {
              continue;
            }

            // Get profile link
            const link = await row.$('a');
            if (!link) continue;

            const linkText = await link.evaluate(el => el.textContent?.trim() || '');
            const url = await link.evaluate(el => el.getAttribute('href') || '');

            if (profileUrls.has(url)) {
              console.log(`[SKIP] Profile already added: ${url}`);
              continue;
            }

            // Get profile info
            const info = await infoTd.evaluate(el => el.textContent?.trim() || '');
            const img = await row.$('img');
            const imgSrc = img ? await img.evaluate(el => el.getAttribute('src') || '') : this.defaultPhotoUrl;

            // Parse profile details
            const infoLines = info.split('\n');
            const title = infoLines[0]?.trim() || linkText;
            const name = infoLines[1]?.trim() || linkText;
            const header = infoLines[2]?.trim() || '';

            // Get email
            let email = '';
            try {
              const emailLink = await row.$('a[href^="mailto"]');
              if (emailLink) {
                email = await emailLink.evaluate(el => el.textContent?.trim().replace('[at]', '@') || '');
              }
            } catch (e) {
              // Email not found
            }

            // Parse keywords
            const { keywords } = this.parseLabelsAndKeywords(info);

            const profile: AcademicProfile = {
              id: profileIdCounter++,
              name,
              title,
              url,
              info,
              photoUrl: imgSrc,
              header,
              green_label,
              blue_label,
              keywords,
              email
            };

            profiles.push(profile);
            profileUrls.add(url);
            console.log(`[ADD] Profile added: ${name} - ${url}`);

            // Check for email match if specified
            if (params.email && email.toLowerCase() === params.email.toLowerCase()) {
              console.log(`[EMAIL_FOUND] Email match found: ${name} - ${email}`);
              break;
            }

            // Check limit
            if (profiles.length >= 100) {
              console.log(`[LIMIT] Reached 100 profile limit`);
              break;
            }

          } catch (e) {
            console.log(`[ERROR] Failed to process profile row: ${e}`);
          }
        }

        if (profiles.length >= 100) break;

        // Try to go to next page
        try {
          const pagination = await page.$('ul.pagination');
          if (!pagination) break;

          const activeLi = await pagination.$('li.active');
          if (!activeLi) break;

          const allLis = await pagination.$$('li');
          const activeIndex = allLis.indexOf(activeLi);
          
          if (activeIndex === allLis.length - 1) {
            console.log('[INFO] Reached last page');
            break;
          }

          const nextLi = allLis[activeIndex + 1];
          const nextA = await nextLi.$('a');
          if (nextA) {
            await nextA.click();
            await page.waitForTimeout(2000);
            pageNum++;
          } else {
            break;
          }
        } catch (e) {
          console.log(`[INFO] Could not navigate to next page: ${e}`);
          break;
        }
      }

      console.log(`[INFO] Total ${profiles.length} profiles collected`);

      // Save results
      const resultData = {
        session_id: sessionId,
        profiles
      };

      const sessionDir = path.join(__dirname, '..', 'main_codes', 'public', 'collaborator-sessions', sessionId);
      fs.mkdirSync(sessionDir, { recursive: true });

      const mainProfilePath = path.join(sessionDir, 'main_profile.json');
      fs.writeFileSync(mainProfilePath, JSON.stringify(resultData, null, 2), 'utf8');

      // Create done file
      const donePath = path.join(sessionDir, 'main_done.txt');
      fs.writeFileSync(donePath, 'completed');

      return {
        success: true,
        sessionId,
        profiles,
        total_profiles: profiles.length
      };

    } catch (error) {
      console.error(`[ERROR] Search failed: ${error}`);
      throw error;
    } finally {
      await page.close();
    }
  }

  public async getAcademicCollaborators(params: CollaboratorParams): Promise<CollaboratorsResponse> {
    const page = await this.createPage();
    const collaborators: Collaborator[] = [];

    try {
      console.log(`[INFO] Getting collaborators for session: ${params.sessionId}, profile: ${params.profileId}`);

      // Load main profile data
      const mainProfilePath = path.join(__dirname, '..', 'main_codes', 'public', 'collaborator-sessions', params.sessionId, 'main_profile.json');
      
      if (!fs.existsSync(mainProfilePath)) {
        throw new Error(`Main profile not found for session: ${params.sessionId}`);
      }

      const mainProfileData = JSON.parse(fs.readFileSync(mainProfilePath, 'utf8'));
      const targetProfile = mainProfileData.profiles.find((p: AcademicProfile) => p.id === params.profileId);

      if (!targetProfile) {
        throw new Error(`Profile ID ${params.profileId} not found in session ${params.sessionId}`);
      }

      console.log(`[INFO] Found target profile: ${targetProfile.name}`);

      // Navigate to profile page
      await page.goto(targetProfile.url);
      
      // Navigate to collaborators tab
      await page.waitForSelector('a[href="viewAuthorGraphs.jsp"]');
      await page.click('a[href="viewAuthorGraphs.jsp"]');
      
      // Wait for graph to load
      await page.waitForFunction(() => {
        const gs = document.querySelectorAll('svg g');
        return gs.length > 2;
      });

      // Get collaborators from graph
      const collaboratorsData = await page.evaluate(() => {
        const gs = document.querySelectorAll('svg g');
        const results: Array<{ name: string; href: string }> = [];
        
        for (let i = 2; i < gs.length; i++) {
          const name = gs[i].querySelector('text')?.textContent?.trim() || '';
          gs[i].dispatchEvent(new MouseEvent('click', { bubbles: true }));
          const href = (document.getElementById('pageUrl') as HTMLAnchorElement)?.href || '';
          results.push({ name, href });
        }
        
        return results;
      });

      console.log(`[INFO] Found ${collaboratorsData.length} collaborators`);

      // Process each collaborator
      for (let idx = 0; idx < collaboratorsData.length; idx++) {
        const { name, href } = collaboratorsData[idx];
        
        let collaborator: Collaborator = {
          id: idx + 1,
          name,
          title: '',
          info: '',
          green_label: '',
          blue_label: '',
          keywords: '',
          photoUrl: this.defaultPhotoUrl,
          status: 'completed',
          deleted: false,
          url: href,
          email: ''
        };

        if (href) {
          try {
            await page.goto(href);
            
            const infoTd = await page.$('td h6');
            if (infoTd) {
              const info = await infoTd.evaluate(el => el.textContent?.trim() || '');
              const infoLines = info.split('\n');
              
              collaborator.title = infoLines[0]?.trim() || name;
              collaborator.name = infoLines[1]?.trim() || name;
              collaborator.info = infoLines[2]?.trim() || '';
              
              // Parse labels and keywords
              const { green_label, blue_label, keywords } = this.parseLabelsAndKeywords(info);
              collaborator.green_label = green_label;
              collaborator.blue_label = blue_label;
              collaborator.keywords = keywords;
              
              // Get email
              try {
                const emailLink = await page.$('a[href^="mailto"]');
                if (emailLink) {
                  collaborator.email = await emailLink.evaluate(el => el.textContent?.trim().replace('[at]', '@') || '');
                }
              } catch (e) {
                // Email not found
              }
              
              // Get photo
              try {
                const img = await page.$('img.img-circle, img#imgPicture');
                if (img) {
                  collaborator.photoUrl = await img.evaluate(el => el.getAttribute('src') || '');
                }
              } catch (e) {
                // Photo not found
              }
            } else {
              collaborator.deleted = true;
              collaborator.url = '';
            }
          } catch (e) {
            console.log(`[ERROR] Failed to process collaborator ${name}: ${e}`);
            collaborator.deleted = true;
            collaborator.url = '';
          }
        } else {
          collaborator.deleted = true;
          collaborator.url = '';
        }

        collaborators.push(collaborator);
        
        // Save progress
        const sessionDir = path.join(__dirname, '..', 'main_codes', 'public', 'collaborator-sessions', params.sessionId);
        const collaboratorsPath = path.join(sessionDir, 'collaborators.json');
        fs.writeFileSync(collaboratorsPath, JSON.stringify(collaborators, null, 2), 'utf8');
        
        await page.waitForTimeout(500); // Small delay for progressive loading
      }

      // Create done file
      if (collaborators.length > 0) {
        const sessionDir = path.join(__dirname, '..', 'main_codes', 'public', 'collaborator-sessions', params.sessionId);
        const donePath = path.join(sessionDir, 'collaborators_done.txt');
        fs.writeFileSync(donePath, 'completed');
      }

      return {
        success: true,
        sessionId: params.sessionId,
        profile: targetProfile,
        collaborators,
        total_collaborators: collaborators.length,
        completed: true,
        status: `✅ Scraping completed! ${collaborators.length} collaborators found.`,
        timestamp: Math.floor(Date.now() / 1000)
      };

    } catch (error) {
      console.error(`[ERROR] Collaborators scraping failed: ${error}`);
      throw error;
    } finally {
      await page.close();
    }
  }

  private getFieldNameById(fieldId: number): string {
    // This would load from fields.json in a real implementation
    const fields = this.loadFields();
    const field = fields.find(f => f.id === fieldId);
    return field?.name || '';
  }

  private loadFields(): any[] {
    try {
      const fieldsPath = path.join(__dirname, '..', 'main_codes', 'public', 'fields.json');
      const fieldsData = fs.readFileSync(fieldsPath, 'utf8');
      return JSON.parse(fieldsData);
    } catch (e) {
      console.error(`[ERROR] Failed to load fields.json: ${e}`);
      return [];
    }
  }

  public async getYokInfo(): Promise<any> {
    return {
      name: "YOK Akademik API",
      description: "Comprehensive database of Turkish university academics",
      baseUrl: this.baseUrl,
      features: [
        "Academic Profile Search",
        "Collaborator Analysis", 
        "Network Mapping",
        "Contact Information"
      ],
      endpoints: [
        "POST /api/search - Search academic profiles",
        "POST /api/collaborators/{sessionId} - Get collaborators"
      ]
    };
  }

  public async cleanup(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }
} 