import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const saved = localStorage.getItem('ids_user');
        if (saved) setUser(JSON.parse(saved));
        setLoading(false);
    }, []);

    const login = (username) => {
        const userData = { username, loginTime: new Date().toISOString() };
        setUser(userData);
        localStorage.setItem('ids_user', JSON.stringify(userData));
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('ids_user');
    };

    if (loading) return null;

    return (
        <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
