from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys

def research():
    co = ChromiumOptions()
    co.auto_port()
    co.headless(False) # As requested
    
    page = ChromiumPage(co)
    
    print("Navigating to PBSO Blotter...")
    page.get('https://www3.pbso.org/blotter/index.cfm')
    
    print("Waiting for page load...")
    if page.wait.ele_displayed('tag:body', timeout=15):
        print("Page loaded.")
        
        # Save HTML
        with open('pbso_dump.html', 'w', encoding='utf-8') as f:
            f.write(page.html)
        print("Saved HTML to pbso_dump.html")
        
        # Find Search Button
        # Guessing common names
        btns = page.eles('tag:button')
        print(f"Found {len(btns)} buttons:")
        for b in btns:
            print(f"  Button: Text='{b.text}', ID='{b.attr('id')}', Class='{b.attr('class')}', Type='{b.attr('type')}'")
            
        inputs = page.eles('tag:input')
        print(f"Found {len(inputs)} inputs:")
        for i in inputs:
            print(f"  Input: Name='{i.attr('name')}', ID='{i.attr('id')}', Type='{i.attr('type')}', Placeholder='{i.attr('placeholder')}'")

        # Try to find a form
        forms = page.eles('tag:form')
        print(f"Found {len(forms)} forms:")
        for f in forms:
            print(f"  Form: Action='{f.attr('action')}', Method='{f.attr('method')}'")

    else:
        print("Page did not load body.")
        
    page.quit()

if __name__ == "__main__":
    research()
