#  Quick Start Guide - Nalytiq Platform

**Get up and running in 5 minutes!**

---

##  Installation (First Time Only)

### **1. Clone & Install**
```bash
# Clone repository
git clone <repository-url>
cd nisr-data-platform

# Frontend dependencies
npm install --legacy-peer-deps

# Backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### **2. Environment Setup**
```bash
# Frontend environment
cp env.example .env.local

# Backend environment
cp backend/env.example backend/.env
```

### **3. Update Environment Variables**
Edit `.env.local`:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Edit `backend/.env`:
```env
SECRET_KEY=your-secret-key-change-this
```

---

##  Daily Development

### **Start Development Servers**

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

### **Access the Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

---

##  Common Tasks

### **Create a User**
1. Go to http://localhost:3000
2. Click "Get Started" or "Register"
3. Fill in:
   - Email: your@email.com
   - Password: (min 8 chars, 1 uppercase, 1 lowercase, 1 number)
   - Role: analyst

### **Upload Data**
1. Login
2. Navigate to "Data Upload"
3. Drop a CSV/Excel/Stata file
4. Wait for automatic analysis
5. View results

### **Export Data**
1. On any table or chart
2. Click "Export" button
3. Choose format (CSV, Excel, JSON)
4. File downloads automatically

---

##  Useful Commands

### **Frontend**
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Lint code
```

### **Backend**
```bash
# Development
python -m uvicorn main:app --reload

# Production
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Check logs
tail -f backend/app.log
```

---

##  Code Examples

### **Upload File (Frontend)**
```typescript
import { useFileUpload } from '@/hooks/use-api'

function UploadComponent() {
  const { upload, loading } = useFileUpload()
  
  const handleUpload = async (file: File) => {
    const result = await upload('/upload/', file)
    console.log('Upload result:', result)
  }
  
  return <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
}
```

### **Show Toast Notification**
```typescript
import { toast } from '@/lib/toast'

// Success
toast.success('Operation completed')

// Error
toast.error('Something went wrong')

// With options
toast.success('File uploaded', {
  title: 'Success',
  duration: 5000,
  action: {
    label: 'View',
    onClick: () => console.log('Clicked')
  }
})
```

### **Form with Validation**
```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { loginSchema, type LoginInput } from '@/lib/validations'

function LoginForm() {
  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' }
  })
  
  const onSubmit = async (data: LoginInput) => {
    // Data is validated automatically
    await login(data)
  }
  
  return <form onSubmit={form.handleSubmit(onSubmit)}>...</form>
}
```

### **Export Data**
```typescript
import { ExportButton } from '@/components/export-button'

function DataTable({ data }) {
  return (
    <>
      <table>...</table>
      <ExportButton data={data} filename="my-data" />
    </>
  )
}
```

### **Add Loading State**
```typescript
import { TableSkeleton } from '@/components/loading-states'

function DataView() {
  const [loading, setLoading] = useState(true)
  
  if (loading) return <TableSkeleton rows={10} columns={5} />
  
  return <table>...</table>
}
```

### **API Call with Error Handling**
```typescript
import { apiClient } from '@/lib/api-client'
import { toast } from '@/lib/toast'

async function loadData() {
  try {
    const data = await apiClient.get('/data')
    toast.success('Data loaded')
    return data
  } catch (error) {
    // Error automatically handled and displayed
    console.error(error)
  }
}
```

---

##  Troubleshooting

### **Backend won't start**
```bash
# Check if port is in use
lsof -i :8000

# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install -r requirements.txt
```

### **Frontend won't start**
```bash
# Clear cache
rm -rf .next node_modules

# Reinstall
npm install --legacy-peer-deps

# Try again
npm run dev
```

### **File upload fails**
- Check file size (max 500MB)
- Check file type (CSV, Excel, Stata only)
- Check backend logs: `tail -f backend/app.log`
- Verify backend is running on port 8000

### **Authentication issues**
- Clear browser localStorage
- Check backend logs for errors
- Verify SECRET_KEY in backend/.env
- Try registering a new user

---

##  File Structure Reference

```
nisr-data-platform/
├── app/                    # Next.js pages
│   ├── (auth)/            # Auth pages
│   ├── (dashboard)/       # Protected pages
│   └── page.tsx           # Landing page
├── components/            # React components
│   ├── ui/               # UI primitives
│   ├── error-boundary.tsx
│   ├── export-button.tsx
│   └── loading-states.tsx
├── lib/                   # Utilities
│   ├── api-client.ts     # API client
│   ├── toast.tsx         # Notifications
│   ├── validations.ts    # Zod schemas
│   └── export-utils.ts   # Export functions
├── hooks/                 # React hooks
│   └── use-api.ts        # API hooks
├── backend/              # Python backend
│   ├── main.py          # FastAPI app
│   ├── auth.py          # Authentication
│   ├── config.py        # Configuration
│   ├── exceptions.py    # Error handling
│   └── validators.py    # Validation
└── Documentation
    ├── README.md        # Main docs
    ├── ENHANCEMENTS.md  # Changes
    ├── DEPLOYMENT.md    # Deploy guide
    └── QUICK_START.md   # This file
```

---

##  UI Component Examples

### **Button with Loading**
```tsx
<Button disabled={loading}>
  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
  Submit
</Button>
```

### **Card with Skeleton**
```tsx
{loading ? (
  <Skeleton className="h-[200px] w-full" />
) : (
  <Card>
    <CardContent>Data here</CardContent>
  </Card>
)}
```

### **Toast on Action**
```tsx
const handleDelete = async () => {
  toast.promise(
    deleteItem(id),
    {
      loading: 'Deleting...',
      success: 'Deleted successfully',
      error: 'Failed to delete'
    }
  )
}
```

---

##  Environment Variables Reference

### **Frontend (.env.local)**
| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_APP_NAME` | App name | `Nalytiq` |
| `NEXT_PUBLIC_ENABLE_CHATBOT` | Enable AI chatbot | `true` |

### **Backend (.env)**
| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | `your-32-char-secret` |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:3000` |
| `MAX_FILE_SIZE_MB` | Max upload size | `500` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

##  Getting Help

### **Documentation**
- Main README: `/README.md`
- API Docs: http://localhost:8000/api/docs
- Enhancements: `/ENHANCEMENTS.md`
- Deployment: `/DEPLOYMENT.md`

### **Logs**
- Backend: `backend/app.log`
- Frontend: Browser console
- Errors: Check error boundary display

### **Support**
- Email: support@nalytiq.rw
- GitHub Issues: [Repository]
- Documentation: Full docs in `/README.md`

---

##  Quick Checklist

Before starting development:
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Dependencies installed
- [ ] Environment files created
- [ ] Both servers running
- [ ] Can access localhost:3000
- [ ] Can access localhost:8000/api/docs

---

##  Next Steps

1. **Explore the UI** - Browse all pages
2. **Upload a file** - Try the data upload feature
3. **Check API docs** - Visit /api/docs
4. **Read main README** - Understand architecture
5. **Review code** - See component examples
6. **Make changes** - Hot reload is active!

---

**Happy Coding! **

*Created by: Chris Mazimpaka*  
*Updated: October 29, 2025*
