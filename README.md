# HackXplore-BluDot

HackXplore-BluDot is a dashboard-based platform for **automated digitization and review of product records**.  
Users can drop files into the dashboard, and the backend processes those records to detect and flag potential errors.

---

## Features

- **Drag-and-drop file upload** for product records
- **Automated backend review pipeline** for document/record analysis
- **Error flagging and tracking dashboard** to monitor record quality
- **Exportable scan results** for audits, reporting, and corrections

---

### Mandatory Requirement (Install First)

- **Poppler `release-26.02.0-0`**  
  This must be installed before running any part of the application to ensure PDF Reading is possible.

### Core Requirements

- **Git** (latest stable)
- **Node.js** (LTS recommended, e.g. 18+)
- **npm** (comes with Node.js) or **yarn**
- **Python 3.10+** (if backend processing services use Python)
- **pip** (Python package manager)
- **Docker** *(optional but recommended for consistent local environments)*

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

Create `.env` files where required (frontend/backend) and set values of:

- API key

Example:

```env
GOOGLE_AI_API_KEY=your_api_key
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

## Suggested Project Structure

```text
HackXplore-BluDot/
├── frontend/            # Dashboard UI
├── backend/             # API + processing logic
├── docs/                # Optional project docs
├── .env        # Environment variable
└── README.md
```

---

## Troubleshooting

- **Dependency errors**: delete `node_modules` and reinstall with `npm install`.
- **Port conflicts**: change `PORT` values in `.env`.
- **Upload/processing failures**: check backend logs and file format constraints.
