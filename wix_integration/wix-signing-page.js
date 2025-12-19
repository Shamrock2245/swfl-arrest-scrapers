/**
 * ============================================================================
 * Wix Signing Page - Velo Code
 * ============================================================================
 * Shamrock Bail Bonds - shamrockbailbonds.biz/sign
 * 
 * This page hosts the SignNow embedded signing iFrame.
 * Signers are directed here via the signing link generated from Dashboard.html
 * 
 * PAGE SETUP IN WIX:
 * 1. Create a new page at /sign
 * 2. Add an HTML iFrame component (name it #signingFrame)
 * 3. Add a loading spinner/text (name it #loadingIndicator)
 * 4. Add a success message container (name it #successMessage)
 * 5. Add an error message container (name it #errorMessage)
 * 6. Paste this code in the page's Velo code editor
 * 
 * URL PARAMETERS:
 * - link: The SignNow embedded signing link (URL encoded)
 * - signer: The signer's name (for display)
 * - role: The signer's role (Defendant, Indemnitor, etc.)
 * ============================================================================
 */

import wixLocation from 'wix-location';
import wixWindow from 'wix-window';

$w.onReady(function () {
    // Get URL parameters
    const query = wixLocation.query;
    const signingLink = query.link ? decodeURIComponent(query.link) : null;
    const signerName = query.signer ? decodeURIComponent(query.signer) : 'Signer';
    const signerRole = query.role ? decodeURIComponent(query.role) : '';
    
    // Initialize UI
    $w('#successMessage').hide();
    $w('#errorMessage').hide();
    
    if (signingLink) {
        // Show loading indicator
        $w('#loadingIndicator').show();
        
        // Set the signing link in the iFrame
        $w('#signingFrame').src = signingLink;
        
        // Wait for iFrame to load
        $w('#signingFrame').onMessage((event) => {
            handleSignNowMessage(event.data);
        });
        
        // Hide loading after a short delay (SignNow doesn't send load events)
        setTimeout(() => {
            $w('#loadingIndicator').hide();
            $w('#signingFrame').expand();
        }, 2000);
        
        // Update page title/header with signer info
        if ($w('#signerInfo')) {
            $w('#signerInfo').text = `${signerRole}: ${signerName}`;
        }
        
    } else {
        // No signing link provided
        $w('#loadingIndicator').hide();
        $w('#signingFrame').collapse();
        $w('#errorMessage').text = 'No signing link provided. Please use the link sent to you via email or SMS.';
        $w('#errorMessage').show();
    }
});

/**
 * Handle messages from SignNow iFrame
 * SignNow sends postMessage events for various actions
 */
function handleSignNowMessage(data) {
    console.log('SignNow message received:', data);
    
    if (data.event === 'signing_complete' || data.type === 'signing_complete') {
        // Signing completed successfully
        showSuccessMessage();
    } else if (data.event === 'signing_declined' || data.type === 'signing_declined') {
        // Signer declined to sign
        showDeclinedMessage();
    } else if (data.event === 'signing_error' || data.type === 'error') {
        // Error occurred during signing
        showErrorMessage(data.message || 'An error occurred during signing.');
    }
}

/**
 * Show success message after signing
 */
function showSuccessMessage() {
    $w('#signingFrame').collapse();
    $w('#successMessage').text = 'Thank you! Your signature has been recorded. You will be redirected shortly.';
    $w('#successMessage').show();
    
    // Redirect to home page after 3 seconds
    setTimeout(() => {
        wixLocation.to('/');
    }, 3000);
}

/**
 * Show declined message
 */
function showDeclinedMessage() {
    $w('#signingFrame').collapse();
    $w('#errorMessage').text = 'You have declined to sign the document. If this was a mistake, please contact Shamrock Bail Bonds.';
    $w('#errorMessage').show();
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    $w('#signingFrame').collapse();
    $w('#errorMessage').text = message;
    $w('#errorMessage').show();
}


/**
 * ============================================================================
 * ALTERNATIVE: Lightbox/Modal Implementation
 * ============================================================================
 * If you prefer to show the signing interface in a modal/lightbox,
 * use this code instead on any page where you want to trigger signing.
 */

// To be called from a button click or link
export function openSigningModal(signingLink, signerName, signerRole) {
    wixWindow.openLightbox('SigningLightbox', {
        link: signingLink,
        signer: signerName,
        role: signerRole
    }).then((result) => {
        if (result && result.signed) {
            // Handle successful signing
            console.log('Document signed successfully');
        }
    });
}


/**
 * ============================================================================
 * LIGHTBOX CODE (SigningLightbox)
 * ============================================================================
 * Create a lightbox named "SigningLightbox" and paste this code there.
 */

/*
import wixWindow from 'wix-window';

$w.onReady(function () {
    const data = wixWindow.lightbox.getContext();
    
    if (data && data.link) {
        $w('#lightboxFrame').src = data.link;
        
        if (data.signer) {
            $w('#lightboxTitle').text = `Signing as: ${data.signer}`;
        }
    }
});

export function closeButton_click(event) {
    wixWindow.lightbox.close({ signed: false });
}

// Call this when signing is complete
function onSigningComplete() {
    wixWindow.lightbox.close({ signed: true });
}
*/
