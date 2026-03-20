import axios from 'axios';

const recApi = axios.create({
  baseURL: import.meta.env.VITE_REC_API_URL ?? 'http://localhost:8000/api/v1',
});

export function setRecApiToken(token: string | null) {
  if (token) {
    recApi.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete recApi.defaults.headers.common['Authorization'];
  }
}

export default recApi;
