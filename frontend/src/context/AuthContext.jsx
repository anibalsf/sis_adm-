import { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { API_URL } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [accessToken, setAccessToken] = useState(() => localStorage.getItem('accessToken'));
    const [refreshToken] = useState(() => localStorage.getItem('refreshToken'));
    const [loading, setLoading] = useState(true);

    axios.defaults.baseURL = API_URL;

    // Interceptor: adjuntar token en cada request
    useEffect(() => {
        const id = axios.interceptors.request.use((config) => {
            const token = localStorage.getItem('accessToken');
            if (token) config.headers.Authorization = `Bearer ${token}`;
            return config;
        });
        return () => axios.interceptors.request.eject(id);
    }, []);

    // Interceptor: auto-refresh cuando el token expira
    useEffect(() => {
        const id = axios.interceptors.response.use(
            (res) => res,
            async (error) => {
                const original = error.config;
                const isAuthUrl = original.url?.includes('/auth/');
                if (error.response?.status === 401 && !isAuthUrl && !original._retry) {
                    original._retry = true;
                    const stored = localStorage.getItem('refreshToken');
                    if (stored) {
                        try {
                            const { data } = await axios.post('/auth/token/refresh/', { refresh: stored });
                            localStorage.setItem('accessToken', data.access);
                            setAccessToken(data.access);
                            original.headers.Authorization = `Bearer ${data.access}`;
                            return axios(original);
                        } catch {
                            clearSession();
                        }
                    } else {
                        clearSession();
                    }
                }
                return Promise.reject(error);
            }
        );
        return () => axios.interceptors.response.eject(id);
    }, []);

    // Cargar usuario al iniciar
    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            axios.get('/auth/me')
                .then((res) => setUser(res.data))
                .catch(() => clearSession())
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    function clearSession() {
        setUser(null);
        setAccessToken(null);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
    }

    async function login(username, password, remember = false) {
        try {
            const { data } = await axios.post('/auth/login', { username, password, remember });
            const { access, refresh, user: userData } = data;

            localStorage.setItem('accessToken', access);
            localStorage.setItem('refreshToken', refresh);
            setAccessToken(access);
            setUser(userData);

            return { success: true, user: userData };
        } catch (error) {
            const msg = error.response?.data?.detail
                || error.response?.data?.non_field_errors?.[0]
                || 'Error al iniciar sesión';
            return { success: false, error: msg };
        }
    }

    async function logout() {
        try {
            const stored = localStorage.getItem('refreshToken');
            if (stored) await axios.post('/auth/logout', { refresh: stored });
        } catch { /* ignorar */ } finally {
            clearSession();
        }
    }

    return (
        <AuthContext.Provider value={{ user, accessToken, login, logout, loading, isAuthenticated: !!user }}>
            {!loading && children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
    return ctx;
}
