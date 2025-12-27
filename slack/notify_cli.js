
import { slackNotify } from './notify.js';

const message = process.argv[2];
const county = process.argv[3] || 'Unknown';

if (!message) {
    console.error('Please provide a message');
    process.exit(1);
}

async function run() {
    try {
        await slackNotify(message, {
            icon_emoji: ':x:',
            username: `Scraper Bot - ${county}`
        });
        console.log('Notification sent');
    } catch (error) {
        console.error('Failed to send notification:', error);
        process.exit(1);
    }
}

run();
