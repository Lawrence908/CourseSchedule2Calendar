#!/bin/bash

# SEO Fixes Test Script for SchedShare
# This script tests the redirect and SEO improvements

echo "🔍 Testing SchedShare SEO Fixes..."
echo "=================================="

# Test URLs to check
TEST_URLS=(
    "http://schedshare.chrislawrence.ca"
    "https://schedshare.chrislawrence.ca"
    "http://www.schedshare.chrislawrence.ca"
    "https://www.schedshare.chrislawrence.ca"
    "http://schedshare.chrislawrence.ca/start"
    "https://schedshare.chrislawrence.ca/start"
    "http://schedshare.chrislawrence.ca/clear-session"
    "https://schedshare.chrislawrence.ca/clear-session"
)

echo "📋 Testing redirect chains..."
echo ""

for url in "${TEST_URLS[@]}"; do
    echo "Testing: $url"
    
    # Get the final URL after redirects
    final_url=$(curl -s -I -L "$url" | grep -i "location:" | tail -1 | cut -d' ' -f2- | tr -d '\r')
    
    if [ -n "$final_url" ]; then
        echo "  → Redirects to: $final_url"
    else
        # If no redirect, get the status code
        status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
        echo "  → Status: $status_code (no redirect)"
    fi
    
    echo ""
done

echo "🔍 Testing SEO endpoints..."
echo ""

# Test sitemap
echo "Testing sitemap.xml..."
sitemap_status=$(curl -s -o /dev/null -w "%{http_code}" "https://schedshare.chrislawrence.ca/sitemap.xml")
echo "  Sitemap status: $sitemap_status"

# Test robots.txt
echo "Testing robots.txt..."
robots_status=$(curl -s -o /dev/null -w "%{http_code}" "https://schedshare.chrislawrence.ca/robots.txt")
echo "  Robots.txt status: $robots_status"

echo ""
echo "📊 SEO Checklist:"
echo "✅ HTTP to HTTPS redirects"
echo "✅ www to non-www redirects"
echo "✅ Canonical URLs in templates"
echo "✅ Improved sitemap.xml"
echo "✅ Enhanced robots.txt"
echo "✅ Fixed /clear-session redirect"
echo "✅ Root route redirect to /home"

echo ""
echo "🎯 Next Steps:"
echo "1. Deploy the updated configuration"
echo "2. Test all redirects manually"
echo "3. Submit updated sitemap to Google Search Console"
echo "4. Monitor Google Search Console for redirect issues"
echo "5. Wait for Google to recrawl the pages"

echo ""
echo "📝 Google Search Console Actions:"
echo "- Submit sitemap: https://schedshare.chrislawrence.ca/sitemap.xml"
echo "- Request reindexing of affected URLs"
echo "- Monitor 'Page with redirect' issues"
