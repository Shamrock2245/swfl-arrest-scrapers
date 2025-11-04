import fetch from 'node-fetch';

/**
 * Send notification to Slack webhook
 * @param {string} message - Message text
 * @param {object} options - Additional options
 */
export async function slackNotify(message, options = {}) {
  const webhookUrl = process.env.SLACK_WEBHOOK_URL;
  
  if (!webhookUrl) {
    // Silently skip if webhook not configured
    return;
  }

  const {
    username = 'SWFL Arrest Scrapers',
    icon_emoji = ':police_car:',
    channel
  } = options;

  const payload = {
    text: message,
    username,
    icon_emoji
  };

  if (channel) {
    payload.channel = channel;
  }

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      console.error('Slack notification failed:', response.statusText);
    }
  } catch (error) {
    console.error('Slack notification error:', error.message);
  }
}

/**
 * Notify about scraper run completion
 */
export async function notifyRunComplete(results) {
  const totalRecords = results.totalRecords || 0;
  const duration = results.duration || 0;
  const successful = results.results?.filter(r => r.success).length || 0;
  const total = results.results?.length || 0;

  const message = `
✅ *SWFL Scrapers Complete*

📊 Total Records: ${totalRecords}
⏱️ Duration: ${duration}s
✅ Successful: ${successful}/${total} counties

${results.results?.map(r => 
  `${r.success ? '✅' : '❌'} ${r.county}: ${r.count || 0} records`
).join('\n')}
  `.trim();

  await slackNotify(message);
}

/**
 * Notify about errors
 */
export async function notifyError(county, error) {
  const message = `
❌ *Scraper Error*

County: ${county}
Error: ${error.message || error}

Check logs for details.
  `.trim();

  await slackNotify(message, { icon_emoji: ':x:' });
}

/**
 * Notify about qualified arrests
 */
export async function notifyQualifiedArrest(record) {
  if (!record.is_qualified) return;

  const message = `
🎯 *New Qualified Arrest*

👤 Name: ${record.full_name_last_first}
💰 Bond: $${record.total_bond}
⚖️ Charge: ${record.charge_1 || 'N/A'}
📍 County: ${record.county}
📊 Score: ${record.qualified_score}/100

<${record.source_url}|View Details>
  `.trim();

  await slackNotify(message, { icon_emoji: ':dart:' });
}

export default slackNotify;
