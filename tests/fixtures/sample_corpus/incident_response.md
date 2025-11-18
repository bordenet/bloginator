# Building Effective Incident Response Teams

*Written: 2023-08-22*
*Tags: incidents, operations, sre, reliability*
*Quality: reference*

The 3am page is inevitable. How your team responds determines whether you have a minor blip or a major outage. After leading incident response for years, here's what actually works.

## The Incident Commander Role

Every incident needs exactly one person in charge: the Incident Commander (IC). Their job isn't to fix the problem - it's to coordinate the response.

The IC:
- Declares incident severity
- Assembles the response team
- Maintains the timeline
- Coordinates communication
- Makes decisions when there's disagreement
- Calls the incident resolved

Rotate the IC role across senior engineers. It builds leadership skills and prevents single points of failure.

## Severity Levels That Make Sense

We use four severity levels:
- **SEV1**: Customer-facing outage, revenue impact
- **SEV2**: Degraded service, workaround available
- **SEV3**: Internal systems affected, no customer impact
- **SEV4**: Minor issues, can wait for business hours

Clear severity levels drive response speed and stakeholder communication.

## The War Room (Virtual or Physical)

Create a dedicated Slack channel for each incident: `#incident-2024-03-15-auth-outage`

All incident communication goes there. No side channels. This keeps everyone aligned and creates an audit trail.

Use a video bridge for SEV1/SEV2 incidents. Seeing faces and sharing screens accelerates troubleshooting.

## The Response Timeline

Document everything in real-time:
```
14:32 - First alerts fire for auth service
14:35 - IC declared, SEV1 established
14:38 - Database connection pool exhausted identified
14:42 - Mitigation: scaled connection pool to 200
14:45 - Service recovery confirmed
15:00 - Incident resolved
```

This timeline becomes the backbone of your postmortem.

## Communication Cadence

For SEV1 incidents, update stakeholders every 15 minutes even if there's no progress. Silence creates anxiety.

Template:
```
**Status Update - 14:45**
Current state: Auth service degraded, ~30% of requests failing
Impact: Login and signup unavailable for web users
Next update: 15:00
Actions in progress: Scaling database connections
ETA: Unknown
```

## Blameless Postmortems

After every SEV1/SEV2, write a postmortem within 48 hours. Focus on systems, not people.

Structure:
1. **What happened** (timeline)
2. **Why it happened** (root cause)
3. **What we did well** (positives!)
4. **What we'll improve** (action items with owners)

Never name individuals. "Engineer X deployed bad code" becomes "Our deployment process didn't catch this edge case."

## The Five Whys

Root cause analysis uses the "five whys" technique:

"Why did the service crash?"
→ Database connections exhausted

"Why were connections exhausted?"
→ Connection leak in new feature

"Why wasn't the leak caught in testing?"
→ Load tests don't simulate this usage pattern

"Why don't load tests cover this?"
→ We don't have realistic production traffic replay

"Why not?"
→ We deprioritized observability tooling

Now we have an actionable root cause: invest in observability.

## Measuring Response Quality

Track these metrics:
- **Time to detect** (first alert to human awareness)
- **Time to acknowledge** (awareness to IC declared)
- **Time to mitigate** (IC declared to customer impact reduced)
- **Time to resolve** (mitigation to full recovery)

Graph these over time. Improving metrics means improving your response capability.

## On-Call Rotation Best Practices

- Rotate weekly (not daily - context switching is expensive)
- Have primary and secondary on-call
- Compensate on-call work (time off or pay)
- Never have same person on-call two weeks in a row
- Automate the rotation (PagerDuty, Opsgenie, etc.)

Burned-out on-call engineers quit. Protect your team.

## Runbooks and Playbooks

For common incident types, maintain runbooks:
```
# Database Connection Saturation

**Symptoms:**
- `db_connection_pool_exhausted` alerts
- Timeouts on all database queries
- Application unable to serve traffic

**Immediate Actions:**
1. Check current connection count: `SHOW PROCESSLIST`
2. Identify long-running queries
3. Scale connection pool temporarily
4. Consider killing longest-running queries

**Root Causes to Investigate:**
- Connection leaks in recent deploys
- Sudden traffic spike
- Slow queries not timing out properly
```

Runbooks turn 30-minute investigations into 5-minute fixes.

## Testing Your Incident Response

Run game days quarterly. Simulate realistic outages:
- Kill a database primary
- Fill up disk space
- Break authentication
- Inject network latency

Use these as training for new ICs and validation that your runbooks work.

## Conclusion

Great incident response is a learned skill backed by good process. Invest in clear roles, communication patterns, and blameless learning.

Your 3am self will thank you.
