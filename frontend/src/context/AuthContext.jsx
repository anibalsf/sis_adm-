import { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { API_URL } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [accessToken, setAccessToken] = useState(localStorage.getItem('accessToken'));
    const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refreshToken'));
    const [loading, setLoading] = useState(true);

    // Configurar baseURL
    axios.defaults.baseURL = API_URL;

    // Interceptor para agregar token a todas las requests
    useEffect(() => {
        const requestInterceptor = axios.interceptors.request.use(
            (config) => {
                if (accessToken) {
                    config.headers.Authorization = `Bearer ${accessToken}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        return () => axios.interceptors.request.eject(requestInterceptor);
    }, [accessToken]);

    // Interceptor para manejar refresh automático
    useEffect(() => {
        const responseInterceptor = axios.interceptors.response.use(
            (response) => response,
            async (error) => {
                const originalRequest = error.config;

                // Si el token expiró y tenemos refresh token
                if (error.response?.status === 401 && refreshToken && !originalRequest._retry) {
                    originalRequest._retry = true;

                    try {
                        const response = await axios.post('/auth/token/refresh/', {
                            refresh: refreshToken
                        });

                        const newAccessToken = response.data.access;
                        setAccessToken(newAccessToken);
                        localStorage.setItem('accessToken', newAccessToken);

                        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                        return axios(originalRequest);
                    } catch (refreshError) {
                        // Si el refresh falla, hacer logout
                        logout();
                        return Promise.reject(refreshError);
                    }
                }

                return Promise.reject(error);
            }
        );

        return () => axios.interceptors.response.eject(responseInterceptor);
    }, [refreshToken]);

    useEffect(() => {
        if (accessToken) {
            loadUser();
        } else {
            setLoading(false);
        }
    }, [accessToken]);

    const loadUser = async () => {
        try {
            const response = await axios.get('/auth/me');
            setUser(response.data);
        } catch (error) {
            console.error('Error loading user:', error);
            logout();
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password, remember = false) => {
        try {
            console.log('🔵 Intentando login...', { username, API_URL });

            const response = await axios.post('/auth/login', { username, password, remember });

            console.log('✅ Login exitoso:', response.data);

            const { access, refresh, user: userData } = response.data;

            setAccessToken(access);
            setRefreshToken(refresh);
            setUser(userData);

            localStorage.setItem('accessToken', access);
            localStorage.setItem('refreshToken', refresh);

            return { success: true };
        } catch (error) {
            console.error('❌ Login error:', error);

            const data = error.response?.data;
            let message = data?.detail;
            if (!message && data && typeof data === 'object') {
                message = (data.non_field_errors && data.non_field_errors[0])
                    || (Array.isArray(Object.values(data)) && Array.isArray(Object.values(data)[0]) ? Object.values(data)[0][0] : undefined);
            }
            return { success: false, error: message || 'Error al iniciar sesión' };
        }
    };

    const logout = async () => {
        try {
            // Intentar blacklistear el refresh token
            if (refreshToken) {
                await axios.post('/auth/logout', { refresh: refreshToken });
            }
        } catch (error) {
            console.error('Error during logout:', error);
        } finally {
            setAccessToken(null);
            setRefreshToken(null);
            setUser(null);
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
        }
    };

    const value = { user, accessToken, login, logout, loading, isAuthenticated: !!user };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
};
