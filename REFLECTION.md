# Reflection – My Experience Using AI Tools for Full-Stack Development

## 👍 What Went Well

* **Code generation was solid**
  When I gave AI very specific instructions, it generated working code right away.

  * Auth system (JWT + bcrypt) → worked out of the box.
  * React components with state management → pretty clean.
  * Dockerfiles → AI even gave me multi-stage builds with caching, which I probably wouldn’t bother with initially.

* **Breaking things into modules worked best**
  I didn’t dump everything at once. Did: Auth → Task CRUD → File upload → WebSockets → Testing/CI.
  This way AI didn’t lose context, and each piece came out decent.

* **Debugging help**
  When I ran into dependency errors or misconfig, AI spotted it fast and gave me multiple fixes. Saved me time googling.

* **Learning along the way**
  I also picked up new stuff: async in FastAPI, React hooks patterns, cleaner Docker builds, better GitHub Actions workflows.
  So it wasn’t just about speed — I learned too.

---

## 👎 What Annoyed Me

* **Config files got overwritten**
  AI sometimes rewrote whole config files. Example: my working GitHub Actions file was just wiped with a new one that didn’t have my custom setup. Had to roll back.

* **Dangerous Docker advice**
  At one point AI told me to run:

  ```bash
  docker system prune -f
  ```

  …which deleted containers from other projects. Yeah, not fun.

* **Needs crazy specific instructions**
  “Add auth” → useless, generic code.
  “Add JWT auth with bcrypt, role-based access, DI in FastAPI” → worked perfectly.
  So you have to spoon-feed it details.

* **Loses context in long chats**
  After long sessions, AI forgot previous architecture and suggested conflicting approaches. I had to keep re-sharing code and structure.

* **Over-engineering**
  AI loves to complicate. For small stuff, it suggested Redux-level state management or heavy design patterns where a couple lines would’ve been enough.

---

## 🎯 Lessons I Picked Up

* Be super specific when asking.
* Work one module at a time, not the whole app.
* Always review commands before running (especially Docker).
* Commit often → easy rollback if AI breaks something.
* Let AI do the boring stuff (boilerplate, CRUD, docs, tests), but keep configs, business logic, and security code under my own control.

---

## My Take

* **Time saved**: from ~a week to just 8–10 hours. Huge.
* **Code quality**: decent starter code, but needed review and polishing.
* **Reliability**: solid for standard use cases and day-to-day dev tasks, and with a bit of review it works fine even on bigger or project-specific parts.
---

## Final Thoughts

For me, AI feels like working with a **super-fast junior dev**. It can generate things in minutes that would take me hours, but it needs supervision and sometimes it does dumb/dangerous things.

Would I use it again? Definitely. But next time I’ll set stricter boundaries, use it module-by-module, and never trust its Docker commands blindly.

---
