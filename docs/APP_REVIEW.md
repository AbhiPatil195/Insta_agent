# Meta App Review Guide (Instagram Messaging)

This guide helps you prepare your app for Meta App Review with Instagram messaging.

## 1) App Setup Checklist
- App mode: switch to Live only after passing review.
- Add products:
  - Instagram Graph API
  - Webhooks
- Roles:
  - Add yourself as Admin/Developer.
  - Add IG Testers (Instagram accounts) under Roles → Instagram Testers; ask testers to accept in the Instagram app.
- Link accounts:
  - Convert Instagram to Business account and connect it to a Facebook Page.
  - Ensure the Page is linked to your app and has messaging enabled.

## 2) Permissions Requested
- instagram_manage_messages: Required to read and reply to IG DMs programmatically.
- pages_messaging: Required for Facebook Page messaging infrastructure that powers IG messaging delivery and actions (mark_seen, typing_on).

## 3) Webhook Configuration
- Callback URL: `https://<your-domain>/webhook`
- Verify token: as set in `.env` → `META_VERIFY_TOKEN`
- Subscription: Instagram → messages
- Signature: We verify `X-Hub-Signature-256` (sha256) and fallback to `X-Hub-Signature` (sha1) with `META_APP_SECRET`.

## 4) Privacy Policy and Data Deletion
- Privacy Policy URL: `https://<your-domain>/privacy`
- Data Deletion URL: `https://<your-domain>/data-deletion`
- In privacy text, explain:
  - What data you collect (IG messages & metadata)
  - Why (to provide automated assistance)
  - How long you retain (configurable; default until deletion request)
  - How to delete (DM “DELETE MY DATA” or contact support)

## 5) Screencast Script (Required)
Record a short video demonstrating:
1. Show the Privacy Policy and Data Deletion pages at the URLs above.
2. Login to Instagram (test account) and send DM to the connected Business account.
3. Show the webhook hitting `/webhook` in logs and the bot replying.
4. Demonstrate a second DM and a memory-based contextual response.
5. Show dashboard at `https://<your-domain>/dash/` (login if required) with message counters updating.
6. Show that “DELETE MY DATA” results in deletion (if implemented) or state the manual process.

## 6) Submission Answers (Examples)
- How you use the permissions:
  - “We need `instagram_manage_messages` and `pages_messaging` to receive and respond to customer DMs on Instagram, mark messages as seen, and provide automated assistance.”
- Data handling:
  - “We store message content and metadata to personalize responses and improve the assistant. We do not sell data. Users can request deletion via DM or contact.”
- Tester credentials:
  - Provide IG tester credentials and the Page/IG handles used for testing.

## 7) Tokens & Configuration
- Generate a long-lived Page Access Token and set `META_PAGE_ACCESS_TOKEN`.
- If available, set `META_IG_BUSINESS_ID` to use `/{IG_BUSINESS_ID}/messages`.
- Keep `META_APP_SECRET` set to enable signature validation.

## 8) Common Pitfalls
- Webhook not publicly accessible or invalid TLS.
- Using Personal (non-Business) IG account.
- Missing permissions subscription for Instagram messages.
- Privacy policy not reachable or not specific.

---

See `docs/TESTING.md` for end-to-end test steps and curl examples.

