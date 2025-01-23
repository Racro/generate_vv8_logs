const puppeteer = require('puppeteer');
const Xvfb = require('xvfb');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const puppeteerExtra = require('puppeteer-extra');
const fs = require('fs');
const yargs = require('yargs');
const { exec } = require('child_process');

var arguments = yargs.argv;
const extn = arguments.extn;
const arg_headless = arguments.headless;
const arg_url = arguments.url;

// Create a new Xvfb instance
const xvfb = new Xvfb({
    silent: true,
    xvfb_args: ['-screen', '0', '1024x768x24', '-ac']
});

// Function to read the cookies.js script
const loadCookiesScript = () => {
    return new Promise((resolve, reject) => {
        fs.readFile('./cookies.js', 'utf8', (err, data) => {
            if (err) {
                reject(err);
            } else {
                resolve(data);
            }
        });
    });
};

// Function to scroll and load more content
async function autoScroll(page) {
    await page.evaluate(async () => {
        await new Promise((resolve, reject) => {
            var totalHeight = 0;
            var distance = 100;
            var timer = setInterval(() => {
                var scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;

                if ((totalHeight >= scrollHeight) || (totalHeight >= 18000)) {
                    clearInterval(timer);
                    resolve();
                }
            }, 100);
        });
    });
}

var pup_args = [
    '--no-sandbox',
    '--disable-web-security',
    '--disable-features=IsolateOrigins,site-per-process',
    '--start-maximized',
    // '--disable-gpu',
];

if (arg_headless == 'true'){
    xvfb.startSync((err)=>{if (err) console.error(err)});
    pup_args.push(`--display=${xvfb._display}`);
    // console.error(`\nXVFB: ${xvfb._display}\n`)
}
if (extn !== 'control'){
    pup_args.push(`--disable-extensions-except=./extn_src/${extn}`);
    pup_args.push(`--load-extension=./extn_src/${extn}`);
}

(async () => {
    args = {
        args: pup_args
    };

    args.executablePath = '/usr/bin/chromium-browser';
    args.headless = false;

    // Launch the browser
    puppeteerExtra.default.use(StealthPlugin());
    // puppeteerExtra.default.launch(args).then(async browser => {
    const browser = await puppeteerExtra.default.launch(args);

    if (extn !== 'control'){
        try {
            await new Promise(r => setTimeout(r, 10000));
            const extensionsPage = await browser.newPage();
            await extensionsPage.goto( 'chrome://extensions', { waitUntil: 'load' } );
            
            await extensionsPage.screenshot({ path: 'extension.png'});

            await extensionsPage.evaluate(`
            chrome.developerPrivate.getExtensionsInfo().then((extensions) => {
                extensions.map((extension) => chrome.developerPrivate.updateExtensionConfiguration({extensionId: extension.id, incognitoAccess: true}));
            });
            `);

        } catch (e) {
            console.error('\n00000000000000\n');
            console.error(e);
            await browser.close();
            throw e;
        };
    }
    
    // await new Promise(r => setTimeout(r, 20000));
    const context = await browser.createIncognitoBrowserContext();
    const page = await context.newPage();
    page.setDefaultTimeout(45000);

    await new Promise(r => setTimeout(r, 5000));

    // URL to visit
    const url1 = 'https://www.geeksforgeeks.org/deletion-in-linked-list/';
    const url2 = 'https://stackoverflow.com/questions/67698176/error-loading-webview-error-could-not-register-service-workers-typeerror-fai'
    const url3 = 'https://www.nytimes.com'
     
    console.error('\nREACHED HERE 1\n');

    tries = 3
    while (tries > 0){
        try{    
            await page.goto(arg_url, { waitUntil: 'networkidle2' });
            await new Promise(r => setTimeout(r, 5000));
            break;
        } catch(e){
            if (tries == 1){
                // exec("rm -rf vv8-*.log", (error, stdout, stderr) => {
                //     console.log(stdout);
                // })
                console.error(`Closing browser due to failed timeouts`);
                // page.close();
                // await browser.close();
            }
            console.error(`Nooooooooooo: ${e}`);
            tries--;
        }
    }

    // Load and execute the cookies.js script
    const cookiesScript = await loadCookiesScript();
    const iframes = await page.evaluate(new Function(cookiesScript));

    for (let iframe=0; iframe<iframes.length; iframe++){
        const subframes = await iframes[iframe].evaluate(new Function(cookiesScript));
        await new Promise(r => setTimeout(r, 2000));
    }
    
    await new Promise(r => setTimeout(r, 2000));
    await autoScroll(page);

    console.error('\nREACHED HERE 2\n');

    page.on('console', msg => {
        for (let i = 0; i < msg.args().length; ++i)
            console.error(`${i}: ${msg.args()[i]}`);
    });


    await page.screenshot({
        path: `screenshot.jpg`
    });

    // await new Promise(r => setTimeout(r, 5000));
    page.close()
    await browser.close();

    // Stop xvfb
    xvfb.stopSync();
})();

