import fetch from 'node-fetch';

const LEE_WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbxtAHChUT0608nVCPd3Rj4tcppgKc8TRfot8Rd5-UkrLqWKSh8Vc4PYhKlyepctr7D5Cw/exec';

/**
 * Triggers the Lee County Scraper running on Google Apps Script
 */
export async function runLee() {
    console.log('📡 Triggering Lee County Scraper (GAS)...');

    try {
        // We pass ?mode=scrape to tell the GAS doScript to run the scraper instead of serving HTML
        // You may need to update the GAS doGet() to handle this parameter!
        const response = await fetch(`${LEE_WEB_APP_URL}?mode=scrape`, {
            method: 'GET',
            follow: 5
        });

        if (response.ok) {
            const text = await response.text();
            console.log('✅ Lee Trigger Sent Successfully');
            // console.log('   Response:', text.substring(0, 100) + '...');

            // If the response is HTML, it might mean it served the page instead of running the script.
            // We count it as success for the trigger itself, but verification is needed in Sheets.
            return { success: true, count: 0, note: 'Triggered Remote Job' };
        } else {
            console.error(`❌ Lee Trigger Failed: ${response.status} ${response.statusText}`);
            return { success: false, count: 0, error: response.statusText };
        }
    } catch (error) {
        console.error(`❌ Lee Trigger Error: ${error.message}`);
        return { success: false, count: 0, error: error.message };
    }
}

// Allow direct execution
if (import.meta.url === `file://${process.argv[1]}`) {
    runLee().then(result => {
        if (!result.success) process.exit(1);
    });
}

export default runLee;
