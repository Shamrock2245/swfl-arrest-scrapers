from scrapling import Fetcher

fetcher = Fetcher()

html = """
<html><body>
    <h1 class="page-title">Smith, John Print</h1>
    <div class="text-right">DOB:</div>
    <div class="col-xs-7">01/01/1980</div>
    <div class="text-right">Race:</div>
    <div class="col-xs-7">W</div>
    <table id="data-table">
        <tr><td>0123</td><td>DUI</td><td></td><td></td><td>5000</td><td></td><td>2023-10-01</td></tr>
    </table>
</body></html>
"""

# Let's mock a page
page = fetcher.get("data:text/html," + html)

label_divs = page.css('div.text-right')
for ld in label_divs:
    print("Label:", ld.text)
    # let's try next_sibling
    try:
        # In Selectolax, node.next gives the next node, which might be a text node, so next_element or similar might be needed. Or find next sibling element.
        print("next:", ld.next.text)
    except Exception as e:
         print("Error on next:", e)
         
    try:
        # if ld is an Adaptor
        nodes = ld._node.next
        while nodes and nodes.tag == '-text':
            nodes = nodes.next
        if nodes:
            print("Selectolax next element:", nodes.text())
    except Exception as e:
        print("Error on internal next:", e)
