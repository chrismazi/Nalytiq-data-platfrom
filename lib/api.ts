export async function uploadDataset(file: File) {
  console.log('Uploading file:', file.name, 'Size:', file.size);
  const formData = new FormData();
  formData.append('file', file);
  console.log('FormData created, sending request...');
  const res = await fetch('http://localhost:8000/upload/', {
    method: 'POST',
    body: formData,
  });
  console.log('Response status:', res.status);
  if (!res.ok) {
    const errorText = await res.text();
    console.error('Upload failed:', errorText);
    throw new Error('Failed to upload dataset');
  }
  const result = await res.json();
  console.log('Upload successful:', result);
  return result;
}

export async function getProfileReport(file: File) {
  console.log('Getting profile report for:', file.name);
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('http://localhost:8000/profile/', {
    method: 'POST',
    body: formData,
  });
  console.log('Profile response status:', res.status);
  if (!res.ok) {
    const errorText = await res.text();
    console.error('Profile failed:', errorText);
    throw new Error('Failed to get profile report');
  }
  const result = await res.text();
  console.log('Profile successful, length:', result.length);
  return result; // HTML content
}

export async function registerUser(email: string, password: string, role: string) {
  const res = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, role }),
  });
  if (!res.ok) throw new Error('Registration failed');
  return res.json();
}

export async function loginUser(email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  const res = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  });
  if (!res.ok) throw new Error('Login failed');
  const data = await res.json();
  localStorage.setItem('token', data.access_token);
  return data;
}

export async function getCurrentUser() {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('No token');
  const res = await fetch('http://localhost:8000/auth/me', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch user');
  return res.json();
}

export async function cleanDataset(file: File) {
  console.log('Cleaning file:', file.name, 'Size:', file.size);
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('http://localhost:8000/clean/', {
    method: 'POST',
    body: formData,
  });
  console.log('Clean response status:', res.status);
  if (!res.ok) {
    const errorText = await res.text();
    console.error('Clean failed:', errorText);
    throw new Error('Failed to clean dataset');
  }
  const result = await res.json();
  console.log('Clean successful:', result);
  return result;
} 