# Security reporting

The project is pre-release. There are no supported released versions yet; security
fixes target the current development branch. A classifier output is advisory;
measured quality and security guarantees must not be inferred from model support.

Report a vulnerability through the repository's **Security > Advisories > Report
a vulnerability** interface at
https://github.com/fedrnv/FDEmailClassifier/security/advisories/new if enabled.
Availability of private reporting is not assumed. If unavailable, use the private
contact route published by repository owner https://github.com/fedrnv. If neither
route is available, open a public issue requesting a private security channel
without vulnerability details. Do not publish exploit details while arranging it.

Provide the affected revision/version, platform, impact, reproduction steps and a
minimal synthetic example. Never send production credentials, email bodies,
personal information, access tokens or private training data. Describe sensitive
inputs structurally. Coordinate any additional disclosure with the maintainer.

Maintainers triage the report, agree on a safe reproduction and remediation, and
coordinate an advisory when appropriate. No response-time SLA is offered. Do not
test against systems or accounts without authorization. Discovered credentials
must be revoked through their owner; deleting a committed secret is insufficient.
