# Google Analytics Setup Guide

This app now includes Google Analytics tracking to monitor visitor statistics and usage patterns.

## Setup Steps

### 1. Create a Google Analytics Account
1. Go to [Google Analytics](https://analytics.google.com/)
2. Sign in with your Google account (create one if needed)
3. Click "Start measuring"

### 2. Create a New Property
1. Property name: "Retirement Budget Calculator"
2. Select your reporting timezone
3. Click "Create"

### 3. Create a Web Data Stream
1. Select "Web" as your platform
2. Enter your website URL (e.g., `https://your-app-url.com`)
3. Stream name: "Retirement Calculator Web"
4. Click "Create stream"

### 4. Get Your Measurement ID
1. After creating the stream, you'll see your **Measurement ID** (looks like `G-XXXXXXXXXX`)
2. Copy this ID

### 5. Update the App
1. Open `web_app.py`
2. Find the Google Analytics section (search for "G-XXXXXXXXXX")
3. Replace both instances of `G-XXXXXXXXXX` with your Measurement ID
4. Save the file

### 6. Deploy and View Stats
1. Deploy your app to Streamlit Cloud or your hosting platform
2. Wait a few minutes for data to start flowing
3. Go to your Google Analytics dashboard to view:
   - **Total Visitors**: Real Time → Realtime or Audience → Overview
   - **Visits Today**: Check the date range in the top right
   - **Session Duration**: Engagement metrics
   - **Top Pages**: User Flow
   - Much more!

## Viewing Statistics

### Real-time Tracking
- Go to **Real time** section to see active users
- Updates every 30 seconds

### Daily/Weekly Reports
- **Reports** → **Life cycle** → **Acquisition**
- See total users, sessions, and engagement
- Filter by date range (today, this week, etc.)

### Custom Reports
- Create custom dashboards for metrics you care about
- Track conversion goals if you add them later

## Privacy Note
- Ensure your privacy policy mentions Google Analytics
- Include required GDPR/privacy disclosures if applicable
- Users in EU may require consent management

## Troubleshooting
- **No data appearing?** 
  - Measurement ID may be incorrect - double-check it
  - Wait 24 hours for initial data processing
  - Check browser privacy settings aren't blocking GA
  
- **Want to verify it's working?**
  - Use [Google Analytics Debugger Chrome Extension](https://chrome.google.com/webstore/detail/google-analytics-debugger)
  - Check browser console for any GA errors

## Questions?
Refer to [Google Analytics Help Center](https://support.google.com/analytics/)
