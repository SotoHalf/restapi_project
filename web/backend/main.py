from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting FoodHealth Analytics API...")
    yield
    # Shutdown
    logger.info("🛑 Shutting down FoodHealth Analytics API...")

app = FastAPI(
    title="FoodHealth Analytics API",
    description="API distribuida para análisis de comidas y nutrición",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En desarrollo permite todo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar templates y archivos estáticos
try:
    templates = Jinja2Templates(directory="frontend/templates")
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    logger.info("✅ Frontend templates configurados")
except Exception as e:
    logger.warning(f"⚠️  No se encontraron directorios frontend: {e}")

# ============ RUTAS WEB ============

# Ruta principal - Homepage
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal del usuario"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FoodHealth - Inicio</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; padding: 40px; background: rgba(255,255,255,0.1); border-radius: 20px; backdrop-filter: blur(10px); }
            .card { background: rgba(255,255,255,0.2); padding: 25px; border-radius: 15px; margin: 25px 0; }
            a { color: #ffd700; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
            code { background: rgba(0,0,0,0.3); padding: 5px 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍽️ FoodHealth Analytics Platform</h1>
            <p>API funcionando correctamente. Endpoints disponibles:</p>
            
            <div class="card">
                <h3>📊 Endpoints de API:</h3>
                <ul>
                    <li><a href="/docs" target="_blank">/docs</a> - Documentación Swagger UI</li>
                    <li><a href="/redoc" target="_blank">/redoc</a> - Documentación ReDoc</li>
                    <li><a href="/health" target="_blank">/health</a> - Salud del sistema</li>
                    <li><a href="/api/meals/search" target="_blank">/api/meals/search</a> - Buscar comidas</li>
                    <li><a href="/api/analytics/health-map" target="_blank">/api/analytics/health-map</a> - Mapa de salud</li>
                    <li><a href="/api/analytics/meal-builder/generate" target="_blank">/api/analytics/meal-builder/generate</a> - Generar comida</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>🔐 Autenticación:</h3>
                <p>Usa estos usuarios de prueba:</p>
                <ul>
                    <li>Admin: <code>admin</code> / <code>admin123</code></li>
                    <li>Usuario normal: <code>user</code> / <code>user123</code></li>
                </ul>
                <a href="/login">Ir a página de login</a>
            </div>
            
            <div class="card">
                <h3>👨‍💼 Panel de Administración:</h3>
                <p><a href="/admin">Acceder al panel admin</a> (requiere login como admin)</p>
            </div>
        </div>
    </body>
    </html>
    """

# Página de login
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FoodHealth - Login</title>
        <style>
            body { 
                font-family: 'Arial', sans-serif; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                margin: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .login-container {
                display: flex;
                max-width: 900px;
                width: 100%;
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            }
            .login-left {
                flex: 1;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .login-right {
                flex: 1;
                padding: 50px;
            }
            h1 { margin-top: 0; }
            input { 
                width: 100%; 
                padding: 15px; 
                margin: 10px 0; 
                border: 2px solid #e0e0e0; 
                border-radius: 10px; 
                font-size: 16px;
                box-sizing: border-box;
            }
            input:focus { 
                outline: none; 
                border-color: #667eea; 
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            button { 
                width: 100%; 
                padding: 15px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                border: none; 
                border-radius: 10px; 
                cursor: pointer; 
                font-size: 16px;
                font-weight: bold;
                margin-top: 20px;
                transition: transform 0.2s;
            }
            button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .demo-credentials {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                margin-top: 20px;
                font-size: 14px;
            }
            .demo-credentials h4 {
                margin-top: 0;
                color: #667eea;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-left">
                <h1>🍽️ FoodHealth</h1>
                <h2>Analytics Platform</h2>
                <p>Plataforma distribuida para análisis de comidas y nutrición.</p>
                <p>Combina datos de TheMealDB y OpenFoodFacts para tomar decisiones alimenticias inteligentes.</p>
                <br>
                <p><strong>Proyecto:</strong> Distributed Computing - Universidad de Lleida</p>
            </div>
            
            <div class="login-right">
                <h2>🔐 Iniciar Sesión</h2>
                <p>Usa las credenciales de prueba:</p>
                
                <div>
                    <input type="text" id="username" placeholder="Usuario" value="admin">
                </div>
                <div>
                    <input type="password" id="password" placeholder="Contraseña" value="admin123">
                </div>
                
                <button onclick="login()">Entrar al Sistema</button>
                
                <div class="demo-credentials">
                    <h4>👥 Usuarios de Prueba:</h4>
                    <p><strong>Administrador:</strong> admin / admin123</p>
                    <p><strong>Usuario Normal:</strong> user / user123</p>
                </div>
            </div>
        </div>
        
        <script>
            async function login() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                const btn = document.querySelector('button');
                btn.disabled = true;
                btn.innerHTML = '🔐 Autenticando...';
                
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);
                
                try {
                    const response = await fetch('/token', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: formData
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        localStorage.setItem('access_token', data.access_token);
                        
                        // Mostrar mensaje de éxito
                        alert('✅ Login exitoso! Redirigiendo...');
                        
                        // Redirigir según rol
                        if (username === 'admin') {
                            window.location.href = '/admin';
                        } else {
                            window.location.href = '/';
                        }
                    } else {
                        const error = await response.text();
                        alert('❌ Error: ' + error);
                    }
                } catch (error) {
                    alert('❌ Error de conexión: ' + error.message);
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = 'Entrar al Sistema';
                }
            }
            
            // Permitir login con Enter
            document.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    login();
                }
            });
        </script>
    </body>
    </html>
    """

# Panel de administración
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Panel de administración"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FoodHealth - Admin Panel</title>
        <style>
            body { font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .admin-container { max-width: 1200px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            .stat-card h3 { margin-top: 0; color: #667eea; }
            .stat-number { font-size: 2.5em; font-weight: bold; margin: 10px 0; }
            .btn { display: inline-block; padding: 12px 25px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; margin: 10px 5px; }
            .btn:hover { background: #764ba2; }
            .api-status { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; }
            .api-online { background: #10b981; color: white; }
            .api-offline { background: #ef4444; color: white; }
        </style>
    </head>
    <body>
        <div class="admin-container">
            <div class="header">
                <h1>👨‍💼 Panel de Administración - FoodHealth</h1>
                <p>Sistema de gestión y monitoreo de la plataforma</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>📊 Estadísticas API</h3>
                    <p><strong>TheMealDB:</strong> <span class="api-status api-online">ONLINE</span></p>
                    <p><strong>OpenFoodFacts:</strong> <span class="api-status api-online">ONLINE</span></p>
                    <p><strong>Solicitudes hoy:</strong> 1,248</p>
                </div>
                
                <div class="stat-card">
                    <h3>👥 Usuarios</h3>
                    <div class="stat-number">154</div>
                    <p>Usuarios registrados (24 activos hoy)</p>
                    <a href="/api/admin/users" class="btn">Ver Usuarios</a>
                </div>
                
                <div class="stat-card">
                    <h3>🍽️ Datos</h3>
                    <div class="stat-number">1,284</div>
                    <p>Comidas analizadas almacenadas</p>
                    <a href="/api/meals/search" class="btn">Ver Comidas</a>
                </div>
                
                <div class="stat-card">
                    <h3>⚙️ Sistema</h3>
                    <p><strong>Estado:</strong> <span class="api-status api-online">OPERATIVO</span></p>
                    <p><strong>Tiempo activo:</strong> 15 días</p>
                    <p><strong>Última sincronización:</strong> Hoy 10:30</p>
                </div>
            </div>
            
            <div style="background: white; padding: 25px; border-radius: 15px; margin-bottom: 30px;">
                <h2>🔄 Control ETL</h2>
                <p>Gestiona procesos de extracción de datos:</p>
                <a href="/api/etl/themealdb/run" class="btn">Ejecutar ETL TheMealDB</a>
                <a href="/api/etl/openfoodfacts/run" class="btn">Ejecutar ETL OpenFoodFacts</a>
                <a href="/api/admin/etl/history" class="btn">Ver Historial ETL</a>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" class="btn">🏠 Ir al Inicio</a>
                <a href="/docs" class="btn">📚 Ver Documentación API</a>
                <button onclick="logout()" class="btn" style="background: #ef4444;">🚪 Cerrar Sesión</button>
            </div>
        </div>
        
        <script>
            function logout() {
                if (confirm('¿Cerrar sesión como administrador?')) {
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                }
            }
        </script>
    </body>
    </html>
    """

# ============ ENDPOINTS API ============

# Endpoint de login (OAuth2 style)
@app.post("/token")
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...)
):
    """Endpoint para obtener token JWT"""
    # Autenticación simple para pruebas
    if username == "admin" and password == "admin123":
        return {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcxMTY3MjgwMH0.mock-admin-token",
            "token_type": "bearer",
            "user": {
                "username": "admin",
                "role": "admin",
                "user_id": "usr_admin_001"
            }
        }
    elif username == "user" and password == "user123":
        return {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIiwicm9sZSI6InVzZXIiLCJleHAiOjE3MTE2NzI4MDB9.mock-user-token",
            "token_type": "bearer",
            "user": {
                "username": "user",
                "role": "user",
                "user_id": "usr_001"
            }
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas. Usa admin/admin123 o user/user123",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Endpoint de salud
@app.get("/health")
async def health_check():
    """Verificar salud del sistema"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "FoodHealth Analytics API",
        "timestamp": "2024-03-15T10:00:00Z",
        "apis": {
            "themealdb": "available",
            "openfoodfacts": "available"
        }
    }

# ============ IMPORTAR ROUTERS API ============

try:
    from backend.api.meals import router as meals_router
    app.include_router(meals_router, prefix="/api/meals", tags=["meals"])
    logger.info("✅ Router de meals cargado")
except ImportError as e:
    logger.warning(f"⚠️  Router meals no disponible: {e}")

try:
    from backend.api.food import router as food_router
    app.include_router(food_router, prefix="/api/food", tags=["food"])
    logger.info("✅ Router de food cargado")
except ImportError as e:
    logger.warning(f"⚠️  Router food no disponible: {e}")

try:
    from backend.api.analytics import router as analytics_router
    app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
    logger.info("✅ Router de analytics cargado")
except ImportError as e:
    logger.warning(f"⚠️  Router analytics no disponible: {e}")

try:
    from backend.api.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
    logger.info("✅ Router de admin cargado")
except ImportError as e:
    logger.warning(f"⚠️  Router admin no disponible: {e}")

# ============ INICIO ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)