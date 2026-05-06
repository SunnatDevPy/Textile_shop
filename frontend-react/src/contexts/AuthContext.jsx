import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [baseUrl] = useState('/api');

  useEffect(() => {
    // Check if user is already logged in
    const savedUsername = localStorage.getItem('admin_username');
    const savedPassword = localStorage.getItem('admin_password');

    if (savedUsername && savedPassword) {
      verifyAuth(savedUsername, savedPassword);
    } else {
      setLoading(false);
    }
  }, []);

  const getAuthHeader = (username, password) => {
    return {
      Authorization: `Basic ${btoa(`${username}:${password}`)}`,
    };
  };

  const verifyAuth = async (username, password) => {
    try {
      const response = await fetch(`${baseUrl}/panel/me`, {
        headers: getAuthHeader(username, password),
      });

      if (response.ok) {
        const data = await response.json();
        setUser({
          ...data,
          username,
          password,
        });
        localStorage.setItem('admin_username', username);
        localStorage.setItem('admin_password', password);
      } else {
        logout();
      }
    } catch (error) {
      console.error('Auth verification failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    setLoading(true);
    try {
      console.log('Attempting login...', { username, baseUrl });
      const response = await fetch(`${baseUrl}/panel/me`, {
        headers: getAuthHeader(username, password),
      });

      console.log('Login response:', response.status, response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Login failed:', errorText);
        throw new Error('Login yoki parol noto\'g\'ri');
      }

      const data = await response.json();
      console.log('Login successful:', data);

      setUser({
        ...data,
        username,
        password,
      });
      localStorage.setItem('admin_username', username);
      localStorage.setItem('admin_password', password);
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('admin_username');
    localStorage.removeItem('admin_password');
  };

  const api = async (path, options = {}) => {
    if (!user) {
      throw new Error('Not authenticated');
    }

    const headers = {
      ...getAuthHeader(user.username, user.password),
      ...(options.headers || {}),
    };

    if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${baseUrl}${path}`, {
      ...options,
      headers,
    });

    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json')
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      throw new Error(
        typeof data === 'string' ? data : JSON.stringify(data, null, 2)
      );
    }

    return data;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, api, baseUrl }}>
      {children}
    </AuthContext.Provider>
  );
};
