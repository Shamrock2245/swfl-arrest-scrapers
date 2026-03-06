from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions().set_headless(True)
co.set_argument('--no-sandbox')
page = ChromiumPage(co)
page.get('https://ww2.colliersheriff.org/arrestsearch/Report.aspx')
print(page.html[:1000])
page.quit()
