from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def format_ist(val):
    """Convert a datetime/date/time value to IST string."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc) 
        ist_val = val.astimezone(IST)
        return ist_val.strftime("%Y-%m-%d %I:%M:%S %p IST")
    else:
        return str(val)

from jose import jwt
from passlib.context import CryptContext
import psycopg2
import psycopg2.extras
import os

# ══════════════════════════════════════
# CONFIG
# ══════════════════════════════════════
DATABASE_URL = "postgresql://postgres.glgijxmawtkazbzripor:Mithun%23k%2323%23v@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
SECRET_KEY = "arena-secret-key-2026-super-secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

app = FastAPI(title="Arena Sports Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════
# DATABASE CONNECTION
# ══════════════════════════════════════
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ══════════════════════════════════════
# INIT TABLES
# ══════════════════════════════════════
def init_database():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            college VARCHAR(255),
            role VARCHAR(50) DEFAULT 'organizer',
            verified BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            sport VARCHAR(100) NOT NULL,
            format VARCHAR(100) NOT NULL,
            status VARCHAR(50) DEFAULT 'Registration',
            max_teams INTEGER DEFAULT 16,
            start_date DATE,
            end_date DATE,
            venue VARCHAR(255),
            organizer_id INTEGER REFERENCES users(id),
            prize VARCHAR(100),
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            sport VARCHAR(100) NOT NULL,
            captain VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            players VARCHAR(50) DEFAULT '11',
            college VARCHAR(255),
            tournament_id INTEGER REFERENCES tournaments(id) ON DELETE SET NULL,
            owner_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
            home_team VARCHAR(255) NOT NULL,
            away_team VARCHAR(255) NOT NULL,
            home_score VARCHAR(10) DEFAULT '',
            away_score VARCHAR(10) DEFAULT '',
            match_date DATE,
            match_time TIME,
            venue VARCHAR(255),
            round VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Scheduled',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[OK] Database tables initialized")

init_database()

# ══════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════
class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    college: str
    role: str = "organizer"
    otp: str = ""  # Any OTP accepted

class LoginRequest(BaseModel):
    email: str
    password: str

class TournamentCreate(BaseModel):
    name: str
    sport: str
    format: str
    status: str = "Registration"
    max_teams: int = 16
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    venue: Optional[str] = None
    prize: Optional[str] = None
    description: Optional[str] = None

class TeamCreate(BaseModel):
    name: str
    sport: str
    captain: str
    email: str
    players: str = "11"
    college: Optional[str] = None
    tournament_id: Optional[int] = None

class MatchCreate(BaseModel):
    tournament_id: int
    home_team: str
    away_team: str
    home_score: str = ""
    away_score: str = ""
    match_date: Optional[str] = None
    match_time: Optional[str] = None
    venue: Optional[str] = None
    round: Optional[str] = None
    status: str = "Scheduled"

# ══════════════════════════════════════
# AUTH HELPERS
# ══════════════════════════════════════
def create_token(user_id: int, email: str, name: str, role: str):
    expire = datetime.now(IST) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "name": name, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ══════════════════════════════════════
# SERVE INDEX.HTML
# ══════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
def serve_index():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ══════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════
@app.post("/api/register")
def register(req: RegisterRequest, conn=Depends(get_db)):
    # Any OTP is accepted — just check it's 6 digits (or skip check entirely)
    # No OTP validation at all — any value works
    cur = get_cursor(conn)
    # Check if email exists
    cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = pwd_context.hash(req.password)
    name = f"{req.first_name} {req.last_name}"
    cur.execute(
        "INSERT INTO users (name, email, password_hash, college, role, verified) VALUES (%s, %s, %s, %s, %s, TRUE) RETURNING id",
        (name, req.email, hashed, req.college, req.role)
    )
    user_id = cur.fetchone()["id"]
    conn.commit()
    
    token = create_token(user_id, req.email, name, req.role)
    return {"token": token, "user": {"id": user_id, "name": name, "email": req.email, "role": req.role, "college": req.college}}

@app.post("/api/login")
def login(req: LoginRequest, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute("SELECT * FROM users WHERE email = %s", (req.email,))
    user = cur.fetchone()
    if not user or not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"], user["email"], user["name"], user["role"])
    return {"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"], "college": user.get("college", "")}}

# ══════════════════════════════════════
# TOURNAMENT ROUTES
# ══════════════════════════════════════
@app.get("/api/tournaments")
def get_tournaments(conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute("SELECT * FROM tournaments ORDER BY created_at DESC")
    tournaments = cur.fetchall()
    for t in tournaments:
        # Get teams count
        cur.execute("SELECT COUNT(*) as count FROM teams WHERE tournament_id = %s", (t["id"],))
        t["team_count"] = cur.fetchone()["count"]
        # Get matches
        cur.execute("SELECT * FROM matches WHERE tournament_id = %s ORDER BY match_date", (t["id"],))
        t["matches"] = cur.fetchall()
        # Convert dates to IST strings
        for key in ["start_date", "end_date", "created_at"]:
            if t.get(key):
                t[key] = format_ist(t[key])
        for m in t["matches"]:
            for key in ["match_date", "match_time", "created_at"]:
                if m.get(key):
                    m[key] = format_ist(m[key])
    return tournaments

@app.post("/api/tournaments")
def create_tournament(req: TournamentCreate, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute(
        """INSERT INTO tournaments (name, sport, format, status, max_teams, start_date, end_date, venue, prize, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (req.name, req.sport, req.format, req.status, req.max_teams,
         req.start_date or None, req.end_date or None, req.venue, req.prize, req.description)
    )
    tid = cur.fetchone()["id"]
    conn.commit()
    return {"id": tid, "message": "Tournament created"}

@app.put("/api/tournaments/{tid}")
def update_tournament(tid: int, req: TournamentCreate, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute(
        """UPDATE tournaments SET name=%s, sport=%s, format=%s, status=%s, max_teams=%s,
        start_date=%s, end_date=%s, venue=%s, prize=%s, description=%s WHERE id=%s""",
        (req.name, req.sport, req.format, req.status, req.max_teams,
         req.start_date or None, req.end_date or None, req.venue, req.prize, req.description, tid)
    )
    conn.commit()
    return {"message": "Tournament updated"}

@app.delete("/api/tournaments/{tid}")
def delete_tournament(tid: int, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute("DELETE FROM tournaments WHERE id = %s", (tid,))
    conn.commit()
    return {"message": "Tournament deleted"}

# ══════════════════════════════════════
# TEAM ROUTES
# ══════════════════════════════════════
@app.get("/api/teams")
def get_teams(conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute("""
        SELECT t.*, tr.name as tournament_name 
        FROM teams t 
        LEFT JOIN tournaments tr ON t.tournament_id = tr.id 
        ORDER BY t.created_at DESC
    """)
    teams = cur.fetchall()
    for t in teams:
        if t.get("created_at"):
            t["created_at"] = format_ist(t["created_at"])
    return teams

@app.post("/api/teams")
def create_team(req: TeamCreate, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute(
        """INSERT INTO teams (name, sport, captain, email, players, college, tournament_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (req.name, req.sport, req.captain, req.email, req.players, req.college, req.tournament_id or None)
    )
    team_id = cur.fetchone()["id"]
    conn.commit()
    return {"id": team_id, "message": "Team registered"}

@app.delete("/api/teams/{team_id}")
def delete_team(team_id: int, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute("DELETE FROM teams WHERE id = %s", (team_id,))
    conn.commit()
    return {"message": "Team removed"}

# ══════════════════════════════════════
# MATCH ROUTES
# ══════════════════════════════════════
@app.get("/api/matches")
def get_matches(conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute("""
        SELECT m.*, t.name as tournament_name 
        FROM matches m 
        JOIN tournaments t ON m.tournament_id = t.id 
        ORDER BY m.match_date DESC NULLS LAST
    """)
    matches = cur.fetchall()
    for m in matches:
        for key in ["match_date", "match_time", "created_at"]:
            if m.get(key):
                m[key] = format_ist(m[key])
    return matches

@app.post("/api/matches")
def create_match(req: MatchCreate, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute(
        """INSERT INTO matches (tournament_id, home_team, away_team, home_score, away_score, match_date, match_time, venue, round, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (req.tournament_id, req.home_team, req.away_team, req.home_score, req.away_score,
         req.match_date or None, req.match_time or None, req.venue, req.round, req.status)
    )
    match_id = cur.fetchone()["id"]
    conn.commit()
    return {"id": match_id, "message": "Match added"}

@app.put("/api/matches/{mid}")
def update_match(mid: int, req: MatchCreate, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute(
        """UPDATE matches SET tournament_id=%s, home_team=%s, away_team=%s, home_score=%s, away_score=%s,
        match_date=%s, match_time=%s, venue=%s, round=%s, status=%s WHERE id=%s""",
        (req.tournament_id, req.home_team, req.away_team, req.home_score, req.away_score,
         req.match_date or None, req.match_time or None, req.venue, req.round, req.status, mid)
    )
    conn.commit()
    return {"message": "Match updated"}

@app.delete("/api/matches/{mid}")
def delete_match(mid: int, conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute("DELETE FROM matches WHERE id = %s", (mid,))
    conn.commit()
    return {"message": "Match deleted"}

# ══════════════════════════════════════
# STATS
# ══════════════════════════════════════
@app.get("/api/stats")
def get_stats(conn=Depends(get_db)):
    cur = get_cursor(conn)
    cur.execute("SELECT COUNT(*) as count FROM tournaments")
    t_count = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) as count FROM teams")
    tm_count = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) as count FROM matches")
    m_count = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) as count FROM users")
    u_count = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) as count FROM tournaments WHERE status = 'Live'")
    live_count = cur.fetchone()["count"]
    return {"tournaments": t_count, "teams": tm_count, "matches": m_count, "users": u_count, "live": live_count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)