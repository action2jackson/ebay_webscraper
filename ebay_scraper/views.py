from django.shortcuts import render

def start(request):
    return render(request, "ebay_scraper/start.html") 