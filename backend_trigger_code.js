
/**
 * Triggers a GitHub Action Workflow for the specified county scraper.
 * @param {string} county - The county name (manatee, sarasota, charlotte, hendry)
 * @return {string} Status message
 */
function triggerGithubScraper(county) {
    // CONFIGURATION
    // 1. Get a GitHub PAT (Personal Access Token) with 'workflow' scope
    // 2. File > Project Properties > Script Properties > Add 'GITHUB_PAT'
    var GITHUB_PAT = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT');
    var REPO_OWNER = 'Shamrock2245';
    var REPO_NAME = 'swfl-arrest-scrapers';

    if (!GITHUB_PAT) {
        throw new Error("Missing 'GITHUB_PAT' in Script Properties.");
    }

    // Map county to workflow filename
    var workflows = {
        'manatee': 'scrape_manatee.yml',
        'sarasota': 'scrape_sarasota.yml',
        'charlotte': 'scrape_charlotte.yml',
        'hendry': 'scrape_hendry.yml'
    };

    var workflowFile = workflows[county.toLowerCase()];
    if (!workflowFile) {
        throw new Error("Unknown county: " + county);
    }

    var url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/actions/workflows/' + workflowFile + '/dispatches';

    var payload = {
        "ref": "main" // Branch to run on
    };

    var options = {
        'method': 'post',
        'headers': {
            'Authorization': 'Bearer ' + GITHUB_PAT,
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Google-Apps-Script'
        },
        'contentType': 'application/json',
        'payload': JSON.stringify(payload),
        'muteHttpExceptions': true
    };

    try {
        var response = UrlFetchApp.fetch(url, options);
        var code = response.getResponseCode();
        var text = response.getContentText();

        if (code === 204) {
            return "Successfully triggered " + workflowFile;
        } else {
            throw new Error("GitHub API Error (" + code + "): " + text);
        }
    } catch (e) {
        Logger.log("Error triggering scraper: " + e.toString());
        throw new Error("Failed to contact GitHub: " + e.message);
    }
}
