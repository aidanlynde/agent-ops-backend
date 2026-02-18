# Slush System: End-to-End User Flow & Experience

**Purpose:** Single source of truth for the complete user journey, screens, and touchpoints across **slush-backend**, **slush-frontend**, and **slush-web**. Use for research prompting, product context, and cross-repo alignment.

**Repos:** slush-backend (FastAPI), slush-frontend (React Native / Expo), slush-web (Next.js)

**Last updated:** February 2025

---

## Table of Contents

1. [High-Level System Map](#1-high-level-system-map)
2. [User Acquisition & First Touch](#2-user-acquisition--first-touch)
3. [Authentication Flow (App)](#3-authentication-flow-app)
4. [Onboarding & Profile Setup (App)](#4-onboarding--profile-setup-app)
5. [Core Split Flow (Lender / Host)](#5-core-split-flow-lender--host)
6. [Participant / Payer Flow (Web + App)](#6-participant--payer-flow-web--app)
7. [Group Slush Flow (Trip / Group Expenses)](#7-group-slush-flow-trip--group-expenses)
8. [Rewards, Points & Deals](#8-rewards-points--deals)
9. [Merchant & Admin (slush-web + Backend)](#9-merchant--admin-slush-web--backend)
10. [Backend API Summary](#10-backend-api-summary)
11. [Deep Links & Web URLs](#11-deep-links--web-urls)

---

## 1. High-Level System Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER ACQUISITION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  • slush-web: Landing (index), App Store / Play links, waitlist              │
│  • Merchant QR (r/[code]): Restaurant scan → App download / open            │
│  • Referral / invite links (invite/[join_code], pay/[sessionId])              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         slush-frontend (App)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  Splash → Auth (SignIn/SignUp/2FA/LinkPhone)                                 │
│       → ProfileSetup (NewOnboarding → first split → ShareSession → complete)  │
│       → Main (Home, Sessions, Groups, Rewards, Profile, etc.)                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│   slush-backend       │  │   slush-web            │  │   slush-web            │
│   (FastAPI)           │  │   Participant flows    │  │   Admin / Merchant     │
│   • /users, /auth     │  │   • /pay/[sessionId]   │  │   • /admin             │
│   • /payments         │  │   • /group-slush/[code]│  │   • /r/[code] merchant │
│   • /receipts         │  │   • /invite/[join_code]│  │   • Deals upload (plan)│
│   • /groups           │  │   • /payback/[join_code]│  │   • Merchant stats     │
│   • /deals, /credit-  │  │                        │  │   • QR funnel, OCR     │
│     points, etc.      │  │                        │  │     analytics         │
└───────────────────────┘  └───────────────────────┘  └───────────────────────┘
```

---

## 2. User Acquisition & First Touch

| Touchpoint | Repo | Route / Screen | Purpose |
|------------|------|----------------|--------|
| **Marketing landing** | slush-web | `/` (index), `/landing-v2` | Hero, value prop, App Store / Play Store CTAs |
| **Waitlist** | slush-web | `/waitlist`, `/android-waitlist` | Email signup; backend `POST /waitlist` |
| **Merchant QR at restaurant** | slush-web | `/r/[code]` | Resolve QR code → merchant branding, App Store / Play / deep link; backend `GET /merchants/qr/{code}`, `POST /merchants/qr/{code}/scan` |
| **Referral link** | slush-web | `/invite/[join_code]` | Group invite preview; “Download Slush” or deep link `slush://join-group?code=...`; backend `GET /groups/join-code/{join_code}` |
| **Payment link (session)** | slush-web | `/pay/[sessionId]` | Participant claim & pay flow; backend `GET /payments/sessions/{id}/public`, claim, platform, payment link |
| **Group Slush payback** | slush-web | `/payback/[join_code]` | Group trip payback entry |
| **Group Slush web view** | slush-web | `/group-slush/[code]`, `/group-slush` | Web view of group total and payees; backend `GET /groups/web/{code}` |

**Deep links (app):** `slush://` — e.g. `slush://join-group?code=...` (invite), `slush://auth` (auth stack). Handled in frontend `useDeepLinking` and linking config.

---

## 3. Authentication Flow (App)

**Stack:** `AuthNavigator` (when `!user`).

| Screen | Route name | Backend / behavior |
|--------|------------|---------------------|
| **Sign In** | `SignIn` | Email/password → `POST /users/login`; Google → `POST /users/google/auth`; Apple → `POST /users/apple/auth` |
| **Sign Up** | `SignUp` | `POST /users/` (register) |
| **Forgot Password** | `ForgotPassword` | `POST /users/reset-password/request` |
| **Reset Password** | `ResetPassword` | `POST /users/reset-password/verify` (token in params) |
| **Link Phone** | `LinkPhone` | Optional; `POST /auth/phone/send-code`, verify, `POST /auth/phone/link-phone` |
| **Two-Factor** | `TwoFactor` | Phone 2FA; `POST /auth/phone/verify-code` |

After successful auth, backend returns `user` and optionally `needs_profile_setup`. If `needs_profile_setup === true`, app shows **ProfileSetup** stack; otherwise **Main**.

---

## 4. Onboarding & Profile Setup (App)

**Stack:** `ProfileSetupNavigator` when `user && needsProfileSetup`.  
**Initial route:** `NewOnboarding`. Payment details are collected **after** the first split (on ShareSession success or when navigating to payment profile).

| Screen | Route name | Purpose |
|--------|------------|---------|
| **New Onboarding** | `NewOnboarding` | First-time intro; CTA to “Scan receipt” or “Enter amount” (manual). |
| **Onboarding1 / Onboarding2** | `Onboarding1`, `Onboarding2` | Legacy onboarding steps (still in stack). |
| **BasicProfile** | `BasicProfile` | Name, phone, avatar (not default path; available if needed). |
| **PaymentProfile** | `PaymentProfile` | Venmo/Cash App/Zelle etc.; shown **after first split** when payment setup is required. |
| **ReceiptScan** | `ReceiptScan` | Camera → upload → backend OCR (`POST /receipts/upload-sparrow` or similar). |
| **ManualSlush** | `ManualSlush` | Number pad total → next. |
| **SplitConfig** | `SplitConfig` | Configure participants, amounts, tax/tip; create session. |
| **ReceiptSplitConfig** | `ReceiptSplitConfig` | Assign receipt line items to participants. |
| **ShareSession** | `ShareSession` | Session created; show payment link + QR; share. On “Done” from onboarding: `completeProfileSetup()` → navigate to **Main** (Home). |
| **QRCodeScreen** | `QRCodeScreen` | Full-screen QR for session link. |

**Flow (typical):** NewOnboarding → ManualSlush (or ReceiptScan → ReceiptSplitConfig) → SplitConfig → ShareSession → (optional PaymentProfile if needed) → complete profile setup → **Main** (Home).

---

## 5. Core Split Flow (Lender / Host)

**Context:** User is the one fronting the bill (lender/host). Can be in **ProfileSetup** (first time) or **Main**.

| Step | App screen | Backend / slush-web |
|------|------------|----------------------|
| 1. Enter total | **ManualSlush** (number pad) or **ReceiptScan** → **ReceiptSplitConfig** | Receipt: `POST /receipts/upload-sparrow` (or upload-improved, etc.); optional merchant code for rewards. |
| 2. Configure split | **SplitConfig** | Add participants (pseudo-users), amounts, tax/tip. No API yet; state is local until “Create”. |
| 3. Create session | **SplitConfig** (submit) | **Receipt path:** `POST /receipts/create-session/` with receipt + participants. **Manual path:** `POST /payments/sessions/` with `total_amount`, `participants[]`. |
| 4. Share | **ShareSession** | `GET /payments/sessions/{id}/link` for payment link. QR encodes e.g. `https://slush.app/pay/{sessionId}` (or app-specific). |
| 5. (Optional) QR | **QRCodeScreen** | Same link, full-screen QR. |

**Main stack** also has: **EditPaymentProfile**, **Sessions**, **SessionDetail**, **EditSplit** (edit existing session).

---

## 6. Participant / Payer Flow (Web + App)

**Entry:** Recipient gets payment link (e.g. `https://slush.web/pay/{sessionId}`) or scans QR.

| Step | Where | What happens |
|------|--------|----------------|
| 1. Open link | slush-web `/pay/[sessionId]` | SSR: `GET /payments/sessions/{id}/public` (or backend proxy). Show session total and list of **unclaimed** participants (pseudo-names + amounts). |
| 2. “I’m this person” | Same page | User selects a participant row. |
| 3. Claim | slush-web → backend | `POST /payments/sessions/{sessionId}/participants/{participantId}/claim` (may include name, phone). |
| 4. Choose platform | Same page | Venmo / Cash App / Zelle. `POST /payments/sessions/.../participants/.../platform`. |
| 5. Get payment link | Backend | `GET /payments/sessions/.../participants/.../payment-link` → redirect or show Venmo/Cash App/Zelle deep link or Stripe. |
| 6. Mark complete | Optional | `POST /payments/sessions/.../participants/.../complete` when they’ve paid. |

Backend also: `GET /payments/sessions/{id}/unclaimed`, `POST /payments/sessions/.../validate-claim`. Stripe flow: **stripe_payments** router (e.g. `/stripe/...`) for card payments.

---

## 7. Group Slush Flow (Trip / Group Expenses)

**Concept:** Ongoing group (trip/friends) with receipts and member balances; different from a one-off payment session.

| Step | App screen / slush-web | Backend |
|------|------------------------|--------|
| Create group | **GroupSlush** or **Groups** → create | `POST /groups/` → returns `group_id`, `join_code`. |
| Invite | Share join link/code | Link: e.g. `https://slush.web/invite/[join_code]` or `slush://join-group?code=...`. Backend: `GET /groups/join-code/{join_code}`, `POST /groups/join`. |
| Join (app) | **JoinGroup** (e.g. deep link) | `POST /groups/join` with join code. |
| Add receipt | **ReceiptScan** (with `groupID`) → **ReceiptSplitConfig** or trip flow | `POST /groups/{id}/receipts` or `upload-receipt`; `PUT /groups/{id}/receipts/{receiptId}/assign`. |
| View trip | **TripSummary** (groupID) | `GET /groups/{id}`, receipts, members. |
| View expenses | **Expenses** (groupName, groupID) | Group receipt list. |
| Mark payments | **MemberDetail**, **SessionDetail**-like flows | `POST /groups/{id}/mark-payment`, `mark-payment-bulk`, etc. |
| Finish / lock | **TripSummary** or group actions | `POST /groups/{id}/finish`, `PUT /groups/{id}/lock`. |
| Web view (participant) | slush-web **/group-slush/[code]** | `GET /groups/web/{code}` → group total, payees, amounts. |
| Payback page | slush-web **/payback/[join_code]** | Payback entry for group. |

Other: **Members**, **MemberDetail**, **GroupEdit**, **ExpenseDetail**, **ClaimList**, **GroupCreated**, **MultiplePending**, **MemberDetail** payment link (`GET /groups/.../members/.../payment-link`).

---

## 8. Rewards, Points & Deals

**Credit points:** Earned by lending ($1 lent ≈ 1 point). Backend: `GET /credit-points/dashboard`, `GET /credit-points/sessions/{sessionId}`.

**App screens:** **Rewards**, **Leaderboard**, **Referral**, **Vouchers**, **Challenges**, **MilestoneList**.

| Feature | Backend | App | slush-web |
|--------|---------|-----|-----------|
| Points dashboard | `/credit-points/dashboard` | RewardsScreen | — |
| Leaderboard | `/leaderboard/`, opt-in, my-rank | LeaderboardScreen | — |
| Referrals | `/referrals/`, `/referrals/code`, `/referrals/apply` | ReferralScreen | — |
| Vouchers (legacy) | `/merchants/vouchers/issue`, `my`, `redeem` | VouchersScreen | — |
| **Deals (pilot)** | `/deals` (feed, purchase, my-redemptions), `POST /deals`, `PATCH /deals/{id}/publish` | Deals feed, redeem with points (see REWARDS_APP_BUILD_PLAN) | Merchant deal upload (docs: MERCHANT_DEALS_UPLOAD); admin/merchant deals UI |
| **Rewards groups (pilot)** | `/rewards-groups` (create, list, join, join-by-code) | Required at deal redemption; create/invite group | — |

Pilot flow (see REWARDS_PILOT_MASTER_PLAN, REWARDS_APP_BUILD_PLAN): Merchant creates deal on web → backend sets points cost → deal appears in app feed (by location or session at merchant) → user spends points → gets redemption code/QR → shows at venue.

---

## 9. Merchant & Admin (slush-web + Backend)

**Admin dashboard:** slush-web **/admin** (admin index). Uses backend with admin auth (e.g. token in `admin_token` / proxy).

| Area | slush-web | Backend |
|------|-----------|---------|
| Merchants CRUD | Admin UI | `GET/POST /admin/merchants`, `GET/PATCH/DELETE /admin/merchants/{id}` |
| QR codes | Admin | `POST /admin/merchants/{id}/qr-codes`, `GET`, `DELETE` |
| Reward rules | Admin | `POST /admin/merchants/{id}/reward-rules`, `PATCH/DELETE /admin/reward-rules/{id}` |
| Merchant stats | Admin | `GET /admin/merchants/{id}/stats`, partner-analytics, item-analytics, qr-funnel, export-report |
| OCR / receipt scan analytics | Admin | `GET /admin/receipt-scan/overview`, accuracy, funnel, usage, trends, cost-analysis, quality-samples, dashboard |
| OCR merchant list | Admin | `GET /admin/ocr-merchants`, `GET /admin/ocr-merchants/{name}`, sessions, receipts |
| Aliases | Admin | `PATCH /admin/merchants/{id}/aliases`, `GET .../suggest-aliases` |
| Feedback | Admin | `POST /admin/feedback`, `GET /admin/feedback`, `GET /admin/feedback/stats` |
| Investor metrics | Admin | `GET /admin/investor-metrics` |
| Deals (pilot) | Create/publish deals (see MERCHANT_DEALS_UPLOAD) | `POST /deals?merchant_id=`, `PATCH /deals/{id}/publish`, `GET /deals?merchant_id=` |

**Merchant-facing:** **/r/[code]** = public merchant QR landing (merchant_id, name, slug, logo, reward info); backend `GET /merchants/qr/{code}` or `GET /merchants/by-slug/{slug}`.

---

## 10. Backend API Summary

| Prefix | Purpose |
|--------|--------|
| `/users` | Register, login, refresh, profile, avatar, username, password, delete, phone lookup, Apple/Google auth, reset-password |
| `/auth/phone` | Send code, verify code, link phone |
| `/payments` | Sessions (create, get, list, link, patch split, delete), claim, platform, payment-link, public, status, complete, unclaimed, validate-claim, title, receipt-details |
| `/stripe` | Stripe payment flow for participants |
| `/receipts` | upload, upload-improved, upload-sparrow, upload-advanced, get, list, delete, assign-items, create-session |
| `/groups` | CRUD groups, join, receipts, upload-receipt, assign, mark-payment, mark-payment-bulk, finish, lock, patch, invite, delete member, regenerate-code, join-code, web, portal, member-summary, payment-link, guest-optin, debt-breakdown, etc. |
| `/merchants` | QR resolve, scan, vouchers issue/my/redeem, stats, create, qr-codes, reward-rules (non-admin), list |
| `/admin` | Merchants, QR, reward-rules, stats, overview, qr-scans, ocr-merchants, feedback, investor-metrics, partner-analytics, item-analytics, qr-funnel, export, aliases, receipt-scan/* |
| `/credit-points` | dashboard, sessions/{id} |
| `/leaderboard` | list, opt-in, my-rank |
| `/referrals` | list, code, apply |
| `/deals` | feed, purchase, my-redemptions, create, list, publish |
| `/rewards-groups` | create, list, get, join, join-by-code |
| `/notifications` | device-token, fcm-token, list, mark-read |
| `/system` | process-notifications, notification-stats, health-check, create-test-notification, send-system-announcement, etc. |
| `/chat` | threads create/get, messages |
| `/waitlist` | create, list |
| `/analytics` | qr-events |
| `/feedback` | create, list, stats, health |
| `/internal` | insights/snapshot (internal only) |

---

## 11. Deep Links & Web URLs

| Type | Example | Handled by |
|------|--------|------------|
| App auth | `slush://auth` | Frontend linking config |
| Join group | `slush://join-group?code=ABC123` | useDeepLinking; slush-web invite page can redirect to this |
| Payment link (participant) | `https://<slush-web>/pay/{sessionId}` | slush-web `/pay/[sessionId]` |
| Group invite | `https://<slush-web>/invite/{join_code}` | slush-web `/invite/[join_code]` |
| Group Slush web | `https://<slush-web>/group-slush/{code}` | slush-web; backend `GET /groups/web/{code}` |
| Merchant QR | `https://<slush-web>/r/{code}` | slush-web; backend `GET /merchants/qr/{code}` |
| Backend web alias | `GET /web/{join_code}` | Backend redirects to `/groups/web/{join_code}` |

---

## Document History & Related Docs

- **slush-backend:** README (user flow summary), docs/REWARDS_SYSTEM_SPEC.md, docs/REWARDS_PILOT_MASTER_PLAN.md, docs/features/CREDIT_POINTS.md, docs/features/SLUSH_GROUPS_API.md.
- **slush-frontend:** README, TUTORIAL_IMPLEMENTATION.md (tutorial steps), docs/REWARDS_APP_BUILD_PLAN.md.
- **slush-web:** README, docs/MERCHANT_DEALS_UPLOAD.md, docs/AGENT_OPS_SETUP.md.

Copy or link this file into **slush-backend** and **slush-web** (e.g. `docs/SLUSH_SYSTEM_USER_FLOW.md`) to keep one system-wide reference for flow, screens, and UX.
