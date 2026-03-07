from scrapling import Fetcher
fetcher = Fetcher()
page = fetcher.get("https://cms.revize.com/revize/apps/sarasota/booking.php?bkg=202600002091")
with open("test_booking_page.html", "w") as f:
    f.write(page.text)
