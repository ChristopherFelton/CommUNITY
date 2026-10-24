# CommUNITY — Volunteer Opportunity Platform

## Project Overview

CommUNITY is a web application designed to connect people with community service and volunteer opportunities. Users should be able to browse available opportunities, view details, and eventually sign up to participate. Organizations should eventually be able to post and manage opportunities.

This project is being developed collaboratively for a hackathon.

## Tech Stack

- **Backend:** Python + Flask
- **Database:** Supabase (PostgreSQL)
- **Database integration:** Flask-SQLAlchemy + Psycopg
- **Frontend:** HTML, CSS, JavaScript, and Jinja templates
- **Deployment:** Vercel (planned)
- **Version control:** GitHub

Do not introduce a different frontend framework, backend framework, or database without discussing it with the team first.

## Git Workflow

The project uses separate branches to keep frontend and backend development independent.

- `main`: Stable, integrated version of the application.
- `backend`: Flask routes, database integration, models, and server-side logic.
- `frontend`: HTML templates, CSS, JavaScript, and visual design.

### Rules for contributors and AI coding agents

1. Work only on the assigned branch.
2. Do not commit directly to `main` unless explicitly authorized.
3. Do not overwrite or substantially restructure another contributor's work.
4. Avoid editing backend files when assigned frontend work.
5. Do not modify database models, environment configuration, or Flask routes unless necessary and approved.
6. Keep changes focused and explain which files were modified.
7. Do not add dependencies without a clear reason.
8. Never commit passwords, API keys, `.env` files, or other secrets.

## Project Structure

The intended structure is:

```text
CommUNITY/
├── app.py
├── models.py
├── requirements.txt
├── .gitignore
├── .env                  # Local only; never commit
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── opportunities.html
│   ├── opportunity_detail.html
│   ├── create_opportunity.html
│   ├── login.html
│   └── dashboard.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── main.js
    └── images/
```

This is the intended structure, not a requirement to create every file immediately. Coordinate before adding, removing, or moving shared files. Deployment configuration may require adjustments to static asset handling.

## Frontend Requirements

The frontend should use Flask's built-in Jinja templating system.

### Templates

- Use `base.html` for the shared layout, navigation, footer, and common page structure.
- Other pages should extend `base.html` using Jinja's `{% extends %}` and `{% block %}` syntax.
- Keep CSS in `static/css/style.css`.
- Keep JavaScript in `static/js/main.js`.
- Reference static files using Flask's `url_for('static', filename='...')`.
- Use `url_for()` for internal route links instead of hardcoding URLs.
- Do not hardcode opportunity listings into the final templates. They must eventually be populated by backend data.

### Design goals

Create a clean, modern, accessible, responsive website centered around community service.

Prioritize:

- Clear navigation
- Easy opportunity discovery
- Readable opportunity cards
- Obvious dates, locations, and signup actions
- Responsive layouts for desktop and mobile
- Accessible labels, keyboard navigation, and sufficient contrast
- Consistent styling across pages

The frontend may use sample data during development, but clearly separate sample data from the eventual backend-provided data.

## Planned Pages and Routes

These are the proposed routes. Coordinate before changing route names or adding overlapping routes.

| Page | Proposed route | Purpose |
|---|---|---|
| Home | `/` | Introduction and featured opportunities |
| Browse opportunities | `/opportunities` | List available opportunities |
| Opportunity details | `/opportunities/<id>` | Show one opportunity's information |
| Create opportunity | `/opportunities/create` | Form for posting an opportunity |
| Login | `/login` | User login interface |
| Dashboard | `/dashboard` | User's opportunities and signups |

These routes may not all be implemented yet. Frontend contributors should not assume that a route already exists just because it is listed here.

## Data Contract: Opportunities

The backend will provide opportunity data to the templates. Use the following proposed field names consistently:

| Field | Meaning |
|---|---|
| `id` | Unique opportunity identifier |
| `title` | Opportunity title |
| `description` | Full description |
| `location` | Where the event takes place |
| `date` | Event date and, if supported, time |
| `capacity` | Maximum number of participants |
| `organizer_id` | Identifier for the organization or user posting it |

For the opportunity listing page, the intended template interface is:

```python
return render_template(
    "opportunities.html",
    opportunities=opportunities
)
```

The template should iterate over `opportunities` and display each item's fields. Backend implementation may evolve, so coordinate if a field's name or format needs to change.

## Forms and Backend Integration

When creating forms, use consistent field names:

### Create opportunity

- `title`
- `description`
- `location`
- `date`
- `capacity`

Use appropriate HTML form methods and action URLs. The backend will validate submitted data; frontend validation is for usability and does not replace server-side validation.

Do not implement fake successful submissions or pretend that data has been saved to Supabase. If the relevant backend route is not available, use clearly identified sample data or a temporary placeholder and document it.

## Backend and Database Boundaries

The backend team owns:

- `app.py` and Flask routes
- `models.py` and SQLAlchemy models
- Database configuration and Supabase integration
- Server-side validation and database writes
- Authentication and authorization logic

Frontend contributors should not connect directly to the database from browser JavaScript. Database credentials must remain server-side.

The frontend should communicate with the backend through Flask routes and Jinja templates unless the team explicitly agrees on another architecture.

## Environment Variables and Security

The application uses a `DATABASE_URL` environment variable to configure its PostgreSQL connection.

- Store local secrets in `.env`.
- Ensure `.env` is listed in `.gitignore`.
- Configure production secrets in the hosting provider's environment-variable settings.
- Never place database credentials in HTML, JavaScript, committed configuration files, or public documentation.
- Do not disable server-side validation or authorization to make a feature work.

## Instructions for AI Coding Agents

Before making changes:

1. Inspect the existing repository and current branch.
2. Read this README and follow the existing code conventions.
3. Identify which files are in scope for your task.
4. Ask for clarification before making significant architectural changes.

When assigned frontend work:

- Focus on templates, styles, and client-side interactions.
- Preserve Flask/Jinja compatibility.
- Do not replace Flask with React, Next.js, or another framework.
- Do not edit database configuration or models.
- Do not invent backend functionality that does not exist.
- Use the agreed route names and opportunity field names.
- If a backend route is missing, report the dependency rather than silently creating or changing backend routes.
- Keep the interface compatible with data supplied by Flask.

After making changes:

1. Summarize the files changed.
2. Explain any assumptions or missing backend dependencies.
3. Provide steps to test the changes.
4. Avoid committing unless specifically asked to do so.

## Definition of Done

A frontend contribution is ready to integrate when:

- The relevant templates render correctly.
- Shared navigation and styling are consistent.
- Links and forms use the agreed route names.
- Templates support backend-provided opportunity data.
- No secrets or unnecessary dependencies were introduced.
- The changes have been tested locally or any testing limitations are documented.

## Current Development Priorities

1. Establish the Flask application and Supabase database connection.
2. Implement the opportunity data model and listing route.
3. Build the frontend around the agreed template and data interfaces.
4. Integrate and test browsing, opportunity creation, and signup functionality.
5. Add authentication and dashboards as time permits.
6. Prepare deployment and a working hackathon demonstration.

When in doubt, preserve the existing architecture and coordinate with the responsible teammate before changing shared interfaces.
