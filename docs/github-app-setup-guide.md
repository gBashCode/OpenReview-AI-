# GitHub App Integration Setup Guide — OpenReview AI

This guide walks through registering, configuring, and connecting a production-ready GitHub App for **OpenReview AI**.

---

## 1. Overview & Architecture

OpenReview AI connects to GitHub via an official GitHub App. The app:
1. Receives real-time PR events (`opened`, `synchronize`, `reopened`, `closed`) via signed HMAC-SHA256 webhooks.
2. Authenticates securely using RS256 JWTs signed with a 2048-bit RSA private key to generate short-lived (1-hour) installation access tokens.
3. Inspects PR file changes and fetches unified diffs (`Accept: application/vnd.github.v3.diff`).
4. Creates GitHub Check Runs (`OpenReview AI / Code Quality`) to track review progress and provide status badges on PR commits.
5. Publishes atomic inline review comments and an executive summary table directly to the Pull Request.

---

## 2. Registering a New GitHub App

1. Log in to GitHub and navigate to:
   - **Personal Account**: [github.com/settings/apps](https://github.com/settings/apps)
   - **Organization Account**: `https://github.com/organizations/<your-org>/settings/apps`
2. Click **New GitHub App**.
3. Fill in the initial application details:
   - **GitHub App name**: `OpenReview AI` (or a unique name like `OpenReview-AI-<org>`)
   - **Homepage URL**: `https://openreview.dev` (or your application domain, e.g. `http://localhost:5173`)
   - **Description**: `Autonomous multi-agent code review platform detecting bugs, security vulnerabilities, and performance regressions.`

---

## 3. URLs and Webhook Configuration

### A. Callback URL
Under **User authorization callback URL**:
```text
https://<your-domain>/api/v1/github/installations/callback
```
*For local development*:
```text
http://localhost:8000/api/v1/github/installations/callback
```

### B. Setup URL (Optional)
Check **Redirect on install** and set **Setup URL**:
```text
http://localhost:5173/dashboard/repositories
```

### C. Webhook Configuration
- Ensure **Active** is checked.
- **Webhook URL**:
  ```text
  https://<your-domain>/api/v1/github/webhook
  ```
  *(For local development, use an ngrok or Smee forwarding URL, e.g. `https://xxxx.ngrok-free.app/api/v1/github/webhook`)*
- **Webhook secret**: Generate a secure secret (e.g. `openssl rand -hex 32`) and save it.
- **SSL verification**: Select **Enable SSL verification**.

---

## 4. Required Permissions

OpenReview AI adheres strictly to the principle of least privilege. Grant only the following permissions:

### Repository Permissions

| Permission | Access Level | Reason |
| :--- | :--- | :--- |
| **Pull requests** | **Read and write** | Fetch PR metadata, post inline line-level comments, and publish overall PR reviews. |
| **Contents** | **Read-only** | Fetch changed file blobs, commit trees, and unified diff hunks. |
| **Checks** | **Read and write** | Create and update GitHub Check Runs (`OpenReview AI / Quality Gate`) on the head commit. |
| **Metadata** | **Read-only** | Mandatory default for reading repository name, owner, and visibility. |

### Organization Permissions
*(Optional - only needed if syncing organization members)*
- **Members**: Read-only

---

## 5. Webhook Events Subscription

Under **Subscribe to events**, select:
- [x] **Pull request** (`opened`, `synchronize`, `reopened`, `closed`, `edited`)
- [x] **Installation** (`created`, `deleted`, `suspend`, `unsuspend`)
- [x] **Installation repositories** (`added`, `removed`)
- [x] **Check run** / **Check suite** (optional, for tracking check run actions)

---

## 6. Where Can This GitHub App Be Installed?

- Select **Any account** (to allow any GitHub user or organization to install it on their repositories) or **Only on this account** (for private internal deployments).
- Click **Create GitHub App**.

---

## 7. Generating Private Keys and Environment Variables

After creating the App:

### 1. Generate Private Key
1. Scroll down to the **Private keys** section.
2. Click **Generate a private key**.
3. A `.pem` file will automatically download (e.g. `openreview-ai.2026-11-19.private-key.pem`).
4. Store this securely in `backend/certs/` or set its content as an environment variable.

### 2. Note Application Credentials
Collect the following values from your GitHub App settings page:
- **App ID**: Listed in the "About" section (numeric, e.g. `1048291`)
- **Client ID**: Listed under "Client ID"
- **Client Secret**: Generate a new client secret under "Client secrets"
- **App Slug**: The URL slug of your app (e.g. `openreview-ai`)

### 3. Configure `.env` File
Update your backend environment file (`backend/.env` or root `.env`):

```env
# GitHub App Configuration
GITHUB_APP_ID=1048291
GITHUB_APP_SLUG=openreview-ai
GITHUB_CLIENT_ID=Iv1.xxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=your_32_character_hex_webhook_secret

# Either point to the PEM file path:
GITHUB_APP_PRIVATE_KEY_PATH=certs/github-app.private-key.pem

# OR paste the raw PEM string directly (useful for containerized/cloud deployments):
# GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEA..."
```

---

## 8. Verifying Local Development with Smee / Ngrok

To receive live GitHub webhooks on `http://127.0.0.1:8000`:

1. **Option 1: Using Smee.io (Recommended for GitHub Webhooks)**:
   ```bash
   npm install -g smee-client
   smee --url https://smee.io/<your-unique-channel> --path /api/v1/github/webhook --port 8000
   ```
   Set your GitHub App's Webhook URL to `https://smee.io/<your-unique-channel>`.

2. **Option 2: Using ngrok**:
   ```bash
   ngrok http 8000
   ```
   Set Webhook URL to `https://<subdomain>.ngrok-free.app/api/v1/github/webhook`.

---

## 9. End-to-End Workflow Verification

1. Install the GitHub App on a test repository via:
   ```text
   http://localhost:8000/api/v1/github/installations/connect
   ```
2. Open a Pull Request in the test repository:
   - The webhook payload will be delivered to `/api/v1/github/webhook`.
   - The HMAC-SHA256 signature is verified with `GITHUB_WEBHOOK_SECRET`.
   - Idempotency is checked via `X-GitHub-Delivery`.
   - The Pull Request record is saved or updated in the OpenReview AI database.
   - The autonomous review pipeline executes and submits:
     - A Check Run with `status: completed` and quality annotations.
     - Line-level inline review comments for detected issues.
     - A formatted Markdown review summary table with dimensional scores.
