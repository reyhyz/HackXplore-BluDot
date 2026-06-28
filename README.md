# HackXplore-BluDot

HackXplore-BluDot is a dashboard-based platform for **automated digitization and review of product records**.  
Users can drop files into the dashboard, and the backend processes those records to detect and flag potential errors.

The platform helps teams:
- Upload and process product record files
- Automatically identify record inconsistencies or errors
- Track flagged issues in a dashboard view
- Export functional scan/review outputs for reporting and follow-up

---

## Features

- **Drag-and-drop file upload** for product records
- **Automated backend review pipeline** for document/record analysis
- **Error flagging and tracking dashboard** to monitor record quality
- **Exportable scan results** for audits, reporting, and corrections

---

## Required Tech Stack

Make sure the following are installed before running the project.

### Mandatory Requirement (Install First)

- **Poppler `release-26.02.0-0`**  
  This must be installed before running any part of the application.

### Core Requirements

- **Git** (latest stable)
- **Node.js** (LTS recommended, e.g. 18+)
- **npm** (comes with Node.js) or **yarn**
- **Python 3.10+** (if backend processing services use Python)
- **pip** (Python package manager)
- **Docker** *(optional but recommended for consistent local environments)*

> If your team uses a different runtime (for example only Node.js or only Python), follow the project-specific environment files and dependency manifests.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Itsjbges/HackXplore-BluDot.git
cd HackXplore-BluDot
```

### 2. Install frontend dependencies

If your frontend is in a folder such as `client` or `frontend`:

```bash
cd frontend
npm install
```

### 3. Install backend dependencies

If your backend is in a folder such as `server` or `backend`:

```bash
cd ../backend
npm install
```

If backend uses Python:

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` files where required (frontend/backend) and set values such as:

- API base URL
- Authentication secrets
- File storage paths/buckets

Example:

```env
PORT=5000
JWT_SECRET=your_secret
```

---

## Running the Software

### Start backend

```bash
cd backend
npm run dev
```

(or your project-specific start command)

### Start frontend

```bash
cd frontend
npm run dev
```

Open the dashboard in your browser (commonly `http://localhost:3000` or `http://localhost:5173`).

---

## How It Works

1. **Upload / Drop files** into the dashboard upload area.
2. The **backend processes product records** and runs review logic.
3. The system **flags detected errors** and displays them in the dashboard.
4. Users can **track errors**, review findings, and monitor status.
5. Users can **export functional scan outputs** for sharing and remediation workflows.

---

## Suggested Project Structure

```text
HackXplore-BluDot/
├── frontend/            # Dashboard UI
├── backend/             # API + processing logic
├── docs/                # Optional project docs
├── .env.example         # Environment variable template
└── README.md
```

---

## Troubleshooting

- **Dependency errors**: delete `node_modules` and reinstall with `npm install`.
- **Port conflicts**: change `PORT` values in `.env`.
- **Upload/processing failures**: check backend logs and file format constraints.
