import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { BriefcaseBusiness, FileText, Heart, LayoutDashboard, PenLine, Search, Sparkles } from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001";
const nav = [["Home", LayoutDashboard], ["Find jobs", Search], ["Resume check", FileText], ["Cover letter", PenLine]];

function App() {
  const [page, setPage] = useState("Home");
  const [resume, setResume] = useState(null);
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Sparkles size={19} /></div><span>Job Search AI</span></div>
      <p className="tagline">Simple job search support</p>
      <nav>{nav.map(([name, Icon]) => <button key={name} className={page === name ? "nav-link active" : "nav-link"} onClick={() => setPage(name)}><Icon size={18}/>{name}</button>)}</nav>
      <div className="sidebar-tip"><Heart size={17}/><p><b>Keep it simple</b><br/>One good application is better than ten rushed ones.</p></div>
    </aside>
    <main className="content">
      {page === "Home" && <Home go={setPage} resume={resume} setResume={setResume} />}
      {page === "Find jobs" && <FindJobs resume={resume} />}
      {page === "Resume check" && <ResumeCheck uploadedResume={resume} />}
      {page === "Cover letter" && <CoverLetter />}
    </main>
  </div>;
}

function Header({ eyebrow, title, children }) {
  return <header className="page-header"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{children && <p className="subtitle">{children}</p>}</header>;
}

function Home({ go, resume, setResume }) {
  const [uploading, setUploading] = useState(false); const [error, setError] = useState("");
  async function upload(file) { if (!file) return; setUploading(true); setError(""); try { setResume(await uploadResume(file)); } catch (err) { setError(err.message || "Could not read that resume."); } finally { setUploading(false); } }
  return <><Header eyebrow="YOUR JOB SEARCH, MADE CALM" title="Welcome back!">Use these small steps to move your search forward today.</Header>
    <section className="hero-card"><div><span className="pill">Today’s focus</span><h2>Find a role that fits your skills.</h2><p>Search live jobs, check your resume against a role, then write a clear cover letter.</p><button className="primary" onClick={() => go("Find jobs")}>Find jobs <Search size={17}/></button></div><div className="hero-art"><BriefcaseBusiness size={72}/></div></section>
    <section className="upload-card"><div><p className="eyebrow">START HERE</p><h2>Upload your resume</h2><p>We’ll read the skills in your own PDF or TXT resume and use them to rank live jobs.</p></div><label className="upload-button"><input type="file" accept=".pdf,.txt,application/pdf,text/plain" onChange={e => upload(e.target.files?.[0])}/>{uploading ? "Reading resume…" : "Choose resume"}</label>{error && <p className="upload-error">{error}</p>}{resume && <div className="resume-success"><b>{resume.filename}</b><span>Detected skills</span><div className="chip-row">{resume.profile.skills.map(skill => <span key={skill}>{skill}</span>)}</div><button className="text-button" onClick={() => go("Find jobs")}>Find matching jobs →</button></div>}</section>
    <section className="section"><div className="section-heading"><h2>Your simple plan</h2><span>3 steps</span></div><div className="step-grid">
      <Step number="01" title="Find jobs" text="Search roles by title and skills." onClick={() => go("Find jobs")} />
      <Step number="02" title="Check your resume" text="See matching and missing keywords." onClick={() => go("Resume check")} />
      <Step number="03" title="Write your letter" text="Create a short starting draft." onClick={() => go("Cover letter")} />
    </div></section>
    <section className="small-note"><Sparkles size={18}/><span><b>No complex AI required.</b> Job Search AI uses clear skill matching and simple templates that you can edit.</span></section>
  </>;
}

function Step({ number, title, text, onClick }) { return <button className="step-card" onClick={onClick}><span>{number}</span><h3>{title}</h3><p>{text}</p><em>Open →</em></button>; }

function FindJobs({ resume }) {
  const [form, setForm] = useState({ role: "", location: "Remote", skills: "" });
  const [jobs, setJobs] = useState([]); const [links, setLinks] = useState([]); const [message, setMessage] = useState(""); const [loading, setLoading] = useState(false);
  useEffect(() => { if (resume?.profile?.skills?.length) setForm(current => ({ ...current, skills: resume.profile.skills.join(", ") })); }, [resume]);
  async function search() { if (!form.role.trim()) { setMessage("Add a role to start your search."); return; } setLoading(true); setMessage(""); try { const data = await post("/search-jobs", { ...form, location: form.location || "Remote", work_mode: "remote", skills: form.skills.split(",").map(x => x.trim()).filter(Boolean) }); setJobs(data.jobs || []); setLinks(data.search_links || []); if (!data.jobs?.length) setMessage(`No live ${form.role} listing explicitly names ${form.location}. Use the live location searches below.`); } catch (error) { setJobs([]); setLinks([]); setMessage(error.message || "Could not reach the live job feed right now."); } finally { setLoading(false); } }
  return <><Header eyebrow="JOB SEARCH" title="Find jobs that fit">Results are filtered by your requested location, role, and resume skills.</Header>
    <div className="search-panel"><label>Role<input placeholder="Example: Software Developer" value={form.role} onChange={e => setForm({...form, role:e.target.value})}/></label><label>Location<input placeholder="Example: Remote or Hyderabad" value={form.location} onChange={e => setForm({...form, location:e.target.value})}/></label><label className="skills-field">Your skills <input placeholder="Example: Java, Python, SQL" value={form.skills} onChange={e => setForm({...form, skills:e.target.value})}/></label><button className="primary" onClick={search} disabled={loading}>{loading ? "Searching…" : "Search jobs"}<Search size={17}/></button></div>
    {resume?.profile?.skills?.length ? <p className="resume-note">Using skills from <b>{resume.filename}</b>. You can edit them if needed.</p> : <p className="resume-note">Upload your resume on Home to fill skills automatically, or enter skills yourself.</p>}{message && <p className="notice">{message}</p>}
    {jobs[0]?.location_match_type === "remote_fallback" && <p className="notice">No current listing explicitly names {form.location}. Showing Remote / Worldwide roles that are eligible from your location.</p>}
    {jobs.length === 0 && links.length > 0 && <section className="live-links"><h2>Search current jobs in {form.location}</h2><p>These open live results for <b>{form.role}</b> in the exact location you selected.</p><div>{links.map(link => <a key={link.name} href={link.url} target="_blank" rel="noreferrer">Search {link.name} →</a>)}</div></section>}
    <div className="job-list">{jobs.map(job => <article className="job-card" key={`${job.source}-${job.id}`}><div><div className="job-title"><h2>{job.title}</h2><span>{job.score}% match</span></div><p className="company">{job.company} · {job.location} · {job.source}</p><p>{job.description}</p><small>{job.match_reason}</small>{job.matched_skills?.length > 0 && <p className="company">Your matching skills: {job.matched_skills.join(", ")}</p>}</div><a href={job.url} target="_blank" rel="noreferrer">View job →</a></article>)}</div>
  </>;
}

function ResumeCheck({ uploadedResume }) {
  const [resume, setResume] = useState(uploadedResume?.text || ""); const [job, setJob] = useState(""); const [result, setResult] = useState(null); const [message, setMessage] = useState("");
  useEffect(() => { if (uploadedResume?.text) setResume(uploadedResume.text); }, [uploadedResume]);
  async function check() { if (!resume.trim() || !job.trim()) { setMessage("Paste both your resume and the job description first."); return; } setMessage(""); try { setResult(await post("/job-match", { resume_text: resume, job_description: job })); } catch { setMessage("The resume check is unavailable. Please make sure the API is running."); } }
  return <><Header eyebrow="RESUME CHECK" title="See your match in seconds">Paste your resume and a job description. We only compare clear, relevant skills.</Header><div className="two-column"><label className="textarea-label">Your resume<textarea rows="12" placeholder="Example: Skills: Java, SQL, Git&#10;Projects: Built a job search web app..." value={resume} onChange={e => setResume(e.target.value)}/></label><label className="textarea-label">Job description<textarea rows="12" placeholder="Example: Looking for a developer with Java, SQL, Git, and API experience..." value={job} onChange={e => setJob(e.target.value)}/></label></div><button className="primary" onClick={check}>Check match <FileText size={17}/></button>{message && <p className="notice">{message}</p>}
    {result && <section className="result-card"><div className="match-score"><strong>{result.match_percent}%</strong><span>skill match</span></div><div><h2>A quick, useful summary</h2><p>{result.explanation}</p><div className="chips"><Chip label="Matched" values={result.matched_skills}/><Chip label="Add next" values={result.missing_skills}/></div></div></section>}</>;
}

function Chip({ label, values }) { return <div><h3>{label}</h3><div className="chip-row">{values.length ? values.map(x => <span key={x}>{x}</span>) : <span>Nothing detected yet</span>}</div></div>; }

function CoverLetter() {
  const [form, setForm] = useState({ name: "", title: "", company: "", skills: "" }); const [letter, setLetter] = useState("");
  async function makeLetter() { const data = await post("/generate-cover-letter", { profile: { name: form.name, skills: form.skills.split(",").map(x => x.trim()), projects: ["a practical software project"] }, job_title: form.title, company: form.company, job_description: "building useful and reliable software" }); setLetter(data.cover_letter); }
  return <><Header eyebrow="COVER LETTER" title="Start with a clear draft">A short template you can personalize before sending.</Header><div className="letter-form"><label>Your name<input placeholder="Example: Priya Sharma" value={form.name} onChange={e => setForm({...form,name:e.target.value})}/></label><label>Job title<input placeholder="Example: Software Developer" value={form.title} onChange={e => setForm({...form,title:e.target.value})}/></label><label>Company<input placeholder="Example: Acme Technologies" value={form.company} onChange={e => setForm({...form,company:e.target.value})}/></label><label>Skills<input placeholder="Example: Java, Python, SQL" value={form.skills} onChange={e => setForm({...form,skills:e.target.value})}/></label></div><button className="primary" onClick={makeLetter}>Create draft <PenLine size={17}/></button>{letter && <pre className="letter-output">{letter}</pre>}</>;
}

async function post(path, body) { const response = await fetch(`${API_BASE}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Request failed"); return data; }
async function uploadResume(file) { const body = new FormData(); body.append("file", file); const response = await fetch(`${API_BASE}/upload-resume`, { method: "POST", body }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Resume upload failed."); return data; }
createRoot(document.getElementById("root")).render(<App />);
