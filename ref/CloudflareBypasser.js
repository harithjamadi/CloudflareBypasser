const { connect } = require("puppeteer-real-browser");
const { CFBypasserError } = require('../exceptions/ErrorsObject');
const path = require('path');

/**
 * CloudflareBypasser class for handling Cloudflare protection bypass.
 * This class provides functionality to bypass Cloudflare's protection and obtain necessary cookies.
 */
class CloudflareBypasser {
    /**
     * Creates a new instance of CloudflareBypasser.
     * @param {Object} copperfield - The copperfield instance for logging and configuration
     */
    constructor(copperfield) {
        this.copperfield = copperfield;
    }

    /**
    * Waits for a specific cookie to be present in the browser's cookies.
    * @param {Object} page - Puppeteer page object
    * @param {string} cookieName - Name of the cookie to wait for
    * @param {number} interval - Interval between checks in milliseconds (default: 2000)
    * @param {number} maxAttempts - Maximum number of attempts before timing out (default: 30)
    * @returns {Promise<string>} The value of the found cookie
    * @throws {Error} If cookie is not found after maximum attempts
    */
    async waitForCookie(page, cookieName, interval = 2000, maxAttempts = 30) {
        let attempts = 0;
        while (attempts < maxAttempts) {
            const cookies = await page.cookies();
            const foundCookie = cookies.find(cookie => cookie.name === cookieName);
            if (foundCookie) {
                this.copperfield.logger.printDebug(`✅ Found ${cookieName} cookie`);
                return foundCookie.value;
            }
            this.copperfield.logger.printWarning(`⏳ Attempt ${attempts + 1}: ${cookieName} not found, retrying...`);
            await new Promise(resolve => setTimeout(resolve, interval));
            attempts++;
        }
        throw new Error(`❌ ${cookieName} not found after ${maxAttempts} attempts`);
    }

    async _closeBrowser(browser) {
        if (browser) {
            try {
                await browser.close();
                this.copperfield.logger.printDebug(`Closing real browser.`);
            } catch (err) {
                this.copperfield.logger.printWarning(`Error closing browser: ${err.message}`);
            }
        }
    }

    /**
    * Bypasses Cloudflare protection and returns cookies and user agent.
    * @param {string} url - The URL to bypass Cloudflare protection for
    * @param {Object} options - Configuration options
    * @param {string[]} [options.browserArgs=[]] - Additional arguments for the browser
    *                   Example: ["--window-size=1920,1080", "--disable-gpu"]
    * @param {Object} [options.proxy=null] - Proxy configuration
    *                 Example: {
    *                   host: "proxy.example.com",
    *                   port: 8080,
    *                   username: "user",
    *                   password: "pass"
    *                 }
    * @param {string} [options.waitUntil='networkidle2'] - Page load strategy
    *                 Possible values: 'networkidle0', 'networkidle2', 'load', 'domcontentloaded'
    * @param {number} [options.cookieTimeout=60000] - Maximum time to wait for cookie in milliseconds
    * @param {number} [options.cookieCheckInterval=2000] - Interval between cookie checks in milliseconds
    * @param {boolean} [options.waitForCookie=true] - Whether to wait for the specified cookie
    * @param {string} [options.cookieName='cf_clearance'] - Name of the cookie to wait for
    * @param {number} [options.waitAfterNavigation=0] - Time to wait after navigation in milliseconds
    * @param {boolean} [options.screenshot=false] - Whether to take a screenshot before closing the browser
    * @param {string} [options.screenshotPath='./'] - Directory path for saving screenshot
    * @param {number} [options.maxRetries=3] - Maximum number of retry attempts if an error occurs
    * @returns {Promise<Object>} Object containing cookies and userAgent, pageContent
    * @throws {CFBypasserError} If any error occurs during the bypass process
    *
    * @example
    * // Basic usage with default settings
    * const { cookies, userAgent } = await this.cloudflareBypasser.bypassCF("https://example.com");
    * 
    * @example
    * // Custom browser configuration
    * const { cookies, userAgent } = await this.cloudflareBypasser.bypassCF("https://example.com", {
    *   browserArgs: ["--window-size=1920,1080", "--disable-gpu"]
    * });

    * 
    * @example
    * // With proxy configuration
    * const { cookies, userAgent } = await this.cloudflareBypasser.bypassCF("https://example.com", {
    *   proxy: {
    *     host: "proxy.example.com",
    *     port: 8080,
    *     username: "user",
    *     password: "pass"
    *   }
    * });
    * 
    * @example
    * // Custom cookie settings
    * const { cookies, userAgent } = await this.cloudflareBypasser.bypassCF("https://example.com", {
    *   waitForCookie: true,
    *   cookieName: "custom_cookie",
    *   cookieTimeout: 30000,
    *   cookieCheckInterval: 1000
    * });
    * 
    * @example
    * // With screenshot enabled
    * const { cookies, userAgent } = await this.cloudflareBypasser.bypassCF("https://example.com", {
    *   screenshot: true,
    *   screenshotPath: this.currentFileDir
    * });
    * 
    * @example
    * // Custom navigation settings
    * const { cookies, userAgent } = await this.cloudflareBypasser.bypassCF("https://example.com", {
    *   waitForCookie: false,
    *   waitAfterNavigation: 5000,
    * });
    */
    async bypassCF(url, {
        browserArgs = [],
        proxy = null,
        waitUntil = 'networkidle2',
        cookieTimeout = 60000,
        cookieCheckInterval = 2000,
        waitForCookie = true,
        cookieName = "cf_clearance",
        waitAfterNavigation = 0,
        screenshot = false,
        screenshotPath = './',
        maxRetries = 3
    } = {}) {
        let lastError;
        let currentTry = 1;

        while (currentTry <= maxRetries) {
            try {
                const connectOptions = {
                    headless: false,
                    args: browserArgs,
                    customConfig: {
                        "port": this.copperfield.port
                    },
                    turnstile: true,
                    connectOption: {},
                    disableXvfb: false,
                    ignoreAllFlags: false
                };

                if (this.copperfield.argsObj.proxy) {
                    this.copperfield.logger.printWarning("Running bypassCF with SYSTEM PROXY !!");
                    connectOptions.proxy = {};
                    const [host, port] = this.copperfield.argsObj.proxy.split(':');
                    connectOptions.proxy["host"] = host;
                    connectOptions.proxy["port"] = port;
                    const proxyAuth = this.copperfield.argsObj["proxy-auth"];
                    if (proxyAuth) {
                        const [username, password] = proxyAuth.split(':');
                        connectOptions.proxy["username"] = username;
                        connectOptions.proxy["password"] = password;
                    }
                } else if (proxy) {
                    this.copperfield.logger.printWarning("Running bypassCF with CUSTOM PROXY !!");
                    connectOptions.proxy = proxy;
                }

                if (connectOptions.customConfig.port) {
                    this.copperfield.logger.printDebug(` Connecting real browser on port ${connectOptions.customConfig.port}...`);
                } else {
                    this.copperfield.logger.printDebug(` Connecting real browser on random port...`);
                }

                var { browser, page } = await connect(connectOptions);

                this.copperfield.logger.printDebug(`️ Xvfb display on port ${process.env.DISPLAY}...`);

                await page.goto(url, { waitUntil });

                if (waitAfterNavigation > 0) {
                    await new Promise(resolve => setTimeout(resolve, waitAfterNavigation));
                }

                if (waitForCookie) {
                    await this.waitForCookie(
                        page,
                        cookieName,
                        cookieCheckInterval,
                        Math.floor(cookieTimeout / cookieCheckInterval)
                    );
                }

                const cookies = (await page.cookies())
                    .map(({ partitionKey, ...cookie }) => cookie);

                const userAgent = await browser.userAgent();

                if (screenshot) {
                    const timestamp = new Date().toISOString();
                    const filename = `cloudflare_bypass_${timestamp}.png`;
                    const fullPath = path.join(screenshotPath, filename);

                    await page.screenshot({
                        path: fullPath,
                    });

                    this.copperfield.logger.printDebug(` Screenshot saved to: ${fullPath}`);
                }

                const pageContent = await page.content();

                return { cookies, userAgent, pageContent };
            } catch (err) {
                lastError = err;
                this.copperfield.logger.printWarning(`Attempt ${currentTry} of ${maxRetries} failed: ${err.message}`);

                await this._closeBrowser(browser);

                if (currentTry === maxRetries) {
                    throw new CFBypasserError(lastError, `Error in CloudflareBypasser after ${maxRetries} attempts! - ${lastError}`);
                }

                currentTry++;
            } finally {
                await this._closeBrowser(browser);
            }
        }
    }
}

module.exports = CloudflareBypasser;
 