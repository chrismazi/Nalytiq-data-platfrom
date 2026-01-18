# Nalytiq - NISR Data Analytics Platform

[![Next.js](https://img.shields.io/badge/Next.js-15.2.4-black)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.1.0-blue)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)

> **AI-Powered Data Analytics Platform for Rwanda's National Institute of Statistics**

Transform raw data into actionable insights with automated analysis, interactive dashboards, and AI-powered reporting.

---

## Features

### **Core Capabilities**
- **Multi-Format Support** - Upload CSV, Excel, and Stata files
- **Automated Data Analysis** - Instant insights with AI-powered recommendations
- **Interactive Dashboards** - Real-time visualizations and metrics
- **Advanced Analytics** - Statistical modeling, cross-tabulation, correlations
- **AI Chatbot** - Natural language queries about your data
- **Report Generation** - Automated PDF/Excel reports with narratives
- **Role-Based Access** - Secure authentication and authorization
- **Data Export** - Export results in multiple formats

### **Enhanced Features (Latest)**
- **Comprehensive Error Handling** - User-friendly error messages
- **File Validation** - Size and format validation before processing
- **Request Timeout Handling** - Graceful timeout management
- **Structured Logging** - Detailed logs for debugging
- **API Documentation** - Auto-generated interactive docs
- **Type Safety** - Full TypeScript implementation
- **Environment Configuration** - Easy deployment configuration

---

## Quick Start

### **Prerequisites**
- Node.js 18+ and npm/pnpm
- Python 3.10+
- Git

### **Installation**

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd nisr-data-platform
```

#### 2. Frontend Setup
```bash
# Install dependencies
npm install --legacy-peer-deps

# Create environment file
cp env.example .env.local

# Edit .env.local with your configuration
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

#### 3. Backend Setup
```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp env.example .env

# Edit .env with your configuration
```

### **Running the Application**

#### Start Backend (Terminal 1)
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

#### Start Frontend (Terminal 2)
```bash
npm run dev
```

Frontend will be available at:
- App: http://localhost:3000

---

## Project Structure

```
nisr-data-platform/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication pages
│   │   ├── login/                # Login page
│   │   └── register/             # Registration page
│   ├── (dashboard)/              # Protected dashboard routes
│   │   ├── dashboard/            # Main analytics dashboard
│   │   ├── data-upload/          # Data upload & analysis
│   │   ├── analysis/             # Advanced analysis tools
│   │   ├── reports/              # Report generation
│   │   └── settings/             # User settings
│   ├── page.tsx                  # Landing page
│   ├── layout.tsx                # Root layout
│   └── globals.css               # Global styles
├── backend/                      # FastAPI backend
│   ├── main.py                   # Main API application
│   ├── auth.py                   # Authentication logic
│   ├── data_analysis.py          # Core analysis engine
│   ├── config.py                 # Configuration management
│   ├── exceptions.py             # Custom exceptions
│   ├── validators.py             # Input validators
│   ├── logger.py                 # Logging setup
│   ├── eda.py                    # Exploratory analysis
│   ├── crosstab.py               # Cross-tabulation
│   ├── modeling.py               # ML modeling
│   ├── chatbot.py                # AI chatbot
│   └── requirements.txt          # Python dependencies
├── components/                   # React components
│   ├── app-sidebar.tsx           # Navigation sidebar
│   ├── chatbot-button.tsx        # AI assistant
│   ├── charts/                   # Chart components
│   └── ui/                       # UI primitives (50+)
├── lib/                          # Utilities
│   ├── api.ts                    # Legacy API client
│   ├── api-client.ts             # Enhanced API client
│   └── utils.ts                  # Helper functions
├── public/                       # Static assets
├── package.json                  # Node dependencies
├── tsconfig.json                 # TypeScript config
├── tailwind.config.ts            # TailwindCSS config
├── next.config.mjs               # Next.js config
└── README.md                     # This file
```

---

## Configuration

### **Frontend Environment Variables**

Create `.env.local`:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Nalytiq
NEXT_PUBLIC_ENABLE_CHATBOT=true
NEXT_PUBLIC_ENABLE_REPORTS=true
```

### **Backend Environment Variables**

Create `backend/.env`:
```env
SECRET_KEY=your-super-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
MAX_FILE_SIZE_MB=500
ALLOWED_EXTENSIONS=csv,xlsx,xls,dta
LOG_LEVEL=INFO
```

---

## API Documentation

### **Interactive API Docs**
Visit http://localhost:8000/api/docs for interactive Swagger UI documentation.

### **Key Endpoints**

#### **Authentication**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info
- `PUT /auth/update` - Update user password

#### **Data Processing**
- `POST /upload/` - Upload and analyze dataset
- `POST /profile/` - Generate comprehensive data profile
- `POST /clean/` - Clean and standardize dataset
- `POST /eda/` - Automated exploratory data analysis

#### **Analysis**
- `POST /grouped-stats/` - Group-by aggregations
- `POST /crosstab/` - Cross-tabulation and frequency tables
- `POST /model/` - Run machine learning models
- `POST /top-districts/` - Top districts by metric
- `POST /poverty-by-education/` - Poverty analysis by education
- `POST /poverty-by-gender/` - Poverty analysis by gender
- `POST /poverty-by-province/` - Poverty analysis by province
- `POST /urban-rural-consumption/` - Urban vs rural comparison
- `POST /avg-consumption-by-province/` - Average consumption by province

#### **AI Features**
- `POST /chatbot/` - Ask questions to AI assistant

---

## Features In Detail

### **1. Data Upload & Validation**
- File type detection (CSV, Excel, Stata)
- File size validation (configurable limit)
- Content validation
- Automatic encoding detection
- Progress tracking

### **2. Automated Analysis**
- Descriptive statistics
- Missing value analysis
- Outlier detection
- Correlation matrices
- Data quality warnings
- Automated insights

### **3. Interactive Dashboards**
- Real-time charts (Recharts)
- Responsive design
- Dark mode support
- Exportable visualizations
- Custom date ranges
- Filtering and sorting

### **4. Advanced Analytics**
- **Grouped Statistics**: Aggregate data by any column
- **Cross-Tabulation**: Pivot tables and frequency analysis
- **Statistical Modeling**: Random Forest classifier/regressor
- **Feature Importance**: Understand key drivers
- **Rwanda-Specific**: Pre-configured poverty and consumption analysis

### **5. AI Chatbot**
- Natural language queries
- Context-aware responses
- Data-specific insights
- Powered by Ollama (Gemma 2B)

### **6. Security Features**
- JWT authentication
- Role-based access control
- Secure password hashing (bcrypt)
- CORS protection
- Request validation
- Input sanitization

---

## Error Handling

The platform includes comprehensive error handling:

### **Backend Error Types**
- `FileValidationError` - Invalid file format or size
- `DataProcessingError` - Data analysis failures
- `AuthenticationError` - Login/auth failures
- `ValidationError` - Input validation failures
- `NetworkError` - Connection issues

### **Frontend Error Handling**
- User-friendly error messages
- Automatic retry logic
- Graceful degradation
- Error logging
- Toast notifications

---

## Supported Data Formats

### **Input Formats**
- **CSV** - Comma-separated values
- **Excel** - .xlsx, .xls formats
- **Stata** - .dta format

### **Export Formats**
- **CSV** - Data tables
- **Excel** - Formatted reports
- **PDF** - Professional reports
- **JSON** - API responses

---

## Authentication Flow

1. **Register** - Create account with email and password
2. **Login** - Receive JWT token
3. **Access** - Token stored in localStorage
4. **Authorized Requests** - Token sent in headers
5. **Auto-Logout** - On token expiration

---

## Usage Examples

### **Upload and Analyze Data**
```typescript
// Upload file
const file = new File([data], "mydata.csv");
const result = await apiClient.uploadFile("/upload/", file);

// Access results
console.log(result.columns);  // Column names
console.log(result.shape);    // [rows, cols]
console.log(result.insights); // Automated insights
```

### **Query with AI**
```typescript
// Ask chatbot
const response = await apiClient.post("/chatbot/", {
  question: "What is the average consumption by province?",
  context: { insights: [...], warnings: [...] }
});
```

---

## Deployment

### **Frontend (Vercel/Netlify)**
```bash
npm run build
npm run start
```

### **Backend (Docker)**
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Development

### **Code Quality**
- TypeScript strict mode
- ESLint configuration
- Prettier formatting
- Pre-commit hooks (recommended)

### **Testing**
```bash
# Frontend tests (to be added)
npm run test

# Backend tests (to be added)
pytest
```

---

## License

This project is proprietary software developed for Rwanda's National Institute of Statistics (NISR).

---

## Contributors

- **Chris Mazimpaka** - Lead Developer
- NISR Rwanda - Product Owner

---

## Support

For issues and questions:
- Email: support@nalytiq.rw
- Documentation: http://localhost:8000/api/docs
- GitHub Issues: [Repository Issues]

---

## Roadmap

- [ ] Unit and integration tests
- [ ] Real-time collaboration
- [ ] Advanced ML models
- [ ] Custom visualizations
- [ ] Mobile app
- [ ] Multi-language support (Kinyarwanda, French, English)
- [ ] API rate limiting
- [ ] Caching layer
- [ ] WebSocket support
- [ ] Advanced export options

---

**Built with love for Rwanda**

*Matthew 5:16*
