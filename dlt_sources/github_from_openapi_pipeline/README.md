# github_from_openapi pipeline

Created with [dlt-init-openapi](https://github.com/dlt-hub/dlt-init-openapi) v. 0.1.0

Generated from downloaded spec at `https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json`
## Learn more at

* https://dlthub.com
* https://github.com/dlt-hub/dlt
* https://github.com/dlt-hub/dlt-init-openapi


## Available resources
* _GET /orgs/{org}/settings/billing/actions_ 
  *resource*: billingget_github_actions_billing_org  
  *description*: Gets the summary of the free and paid GitHub Actions minutes used.  Paid minutes only apply to workflows in private repositories that use GitHub-hosted runners. Minutes used is listed for each GitHub-hosted runner operating system. Any job re-runs are also included in the usage. The usage returned includes any minute multipliers for macOS and Windows runners, and is rounded up to the nearest whole minute. For more information, see "[Managing billing for GitHub Actions](https://docs.github.com/github/setting-up-and-managing-billing-and-payments-on-github/managing-billing-for-github-actions)".  OAuth app tokens and personal access tokens (classic) need the `repo` or `admin:org` scope to use this endpoint.
* _GET /users/{username}/settings/billing/actions_ 
  *resource*: billingget_github_actions_billing_user  
  *description*: Gets the summary of the free and paid GitHub Actions minutes used.  Paid minutes only apply to workflows in private repositories that use GitHub-hosted runners. Minutes used is listed for each GitHub-hosted runner operating system. Any job re-runs are also included in the usage. The usage returned includes any minute multipliers for macOS and Windows runners, and is rounded up to the nearest whole minute. For more information, see "[Managing billing for GitHub Actions](https://docs.github.com/github/setting-up-and-managing-billing-and-payments-on-github/managing-billing-for-github-actions)".  OAuth app tokens and personal access tokens (classic) need the `user` scope to use this endpoint.
* _GET /orgs/{org}/actions/cache/usage-by-repository_ 
  *resource*: actionsget_actions_cache_usage_by_repo_for_org  
  *description*: Lists repositories and their GitHub Actions cache usage for an organization. The data fetched using this API is refreshed approximately every 5 minutes, so values returned from this endpoint may take at least 5 minutes to get updated.  OAuth tokens and personal access tokens (classic) need the `read:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/cache/usage_ 
  *resource*: actionsget_actions_cache_usage  
  *description*: Gets GitHub Actions cache usage for a repository. The data fetched using this API is refreshed approximately every 5 minutes, so values returned from this endpoint may take at least 5 minutes to get updated.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /orgs/{org}/actions/cache/usage_ 
  *resource*: actionsget_actions_cache_usage_for_org  
  *description*: Gets the total GitHub Actions cache usage for an organization. The data fetched using this API is refreshed approximately every 5 minutes, so values returned from this endpoint may take at least 5 minutes to get updated.  OAuth tokens and personal access tokens (classic) need the `read:org` scope to use this endpoint.
* _GET /orgs/{org}/actions/permissions/workflow_ 
  *resource*: actionsget_github_actions_default_workflow_permissions_organization  
  *description*: Gets the default workflow permissions granted to the `GITHUB_TOKEN` when running workflows in an organization, as well as whether GitHub Actions can submit approving pull request reviews. For more information, see "[Setting the permissions of the GITHUB_TOKEN for your organization](https://docs.github.com/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization#setting-the-permissions-of-the-github_token-for-your-organization)."  OAuth tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/permissions/workflow_ 
  *resource*: actionsget_github_actions_default_workflow_permissions_repository  
  *description*: Gets the default workflow permissions granted to the `GITHUB_TOKEN` when running workflows in a repository, as well as if GitHub Actions can submit approving pull request reviews. For more information, see "[Setting the permissions of the GITHUB_TOKEN for your repository](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#setting-the-permissions-of-the-github_token-for-your-repository)."  OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /orgs/{org}/actions/permissions_ 
  *resource*: actionsget_github_actions_permissions_organization  
  *description*: Gets the GitHub Actions permissions policy for repositories and allowed actions and reusable workflows in an organization.  OAuth tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}/actions/secrets/public-key_ 
  *resource*: actionsget_org_public_key  
  *description*: Gets your public key, which you need to encrypt secrets. You need to encrypt a secret before you can create or update secrets.  The authenticated user must have collaborator access to a repository to create, update, or read secrets.  OAuth tokens and personal access tokens (classic) need the`admin:org` scope to use this endpoint. If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/secrets/public-key_ 
  *resource*: actionsget_repo_public_key  
  *description*: Gets your public key, which you need to encrypt secrets. You need to encrypt a secret before you can create or update secrets.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/secrets/public-key_ 
  *resource*: actionsget_environment_public_key  
  *description*: Get the public key for an environment, which you need to encrypt environment secrets. You need to encrypt a secret before you can create or update secrets.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/permissions_ 
  *resource*: actionsget_github_actions_permissions_repository  
  *description*: Gets the GitHub Actions permissions policy for a repository, including whether GitHub Actions is enabled and the actions and reusable workflows allowed to run in the repository.  OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/organization-secrets_ 
  *resource*: actionslist_repo_organization_secrets  
  *description*: Lists all organization secrets shared with a repository without revealing their encrypted values.  Authenticated users must have collaborator access to a repository to create, update, or read secrets.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/secrets_ 
  *resource*: actionslist_repo_secrets  
  *description*: Lists all secrets available in a repository without revealing their encrypted values.  Authenticated users must have collaborator access to a repository to create, update, or read secrets.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/secrets/{secret_name}_ 
  *resource*: actionsget_repo_secret  
  *description*: Gets a single repository secret without revealing its encrypted value.  The authenticated user must have collaborator access to the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/secrets_ 
  *resource*: actionslist_environment_secrets  
  *description*: Lists all secrets available in an environment without revealing their encrypted values.  Authenticated users must have collaborator access to a repository to create, update, or read secrets.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/secrets/{secret_name}_ 
  *resource*: actionsget_environment_secret  
  *description*: Gets a single environment secret without revealing its encrypted value.  Authenticated users must have collaborator access to a repository to create, update, or read secrets.  OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/organization-variables_ 
  *resource*: actionslist_repo_organization_variables  
  *description*: Lists all organization variables shared with a repository.  Authenticated users must have collaborator access to a repository to create, update, or read variables.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/variables_ 
  *resource*: actionslist_repo_variables  
  *description*: Lists all repository variables.  Authenticated users must have collaborator access to a repository to create, update, or read variables.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/variables/{name}_ 
  *resource*: actionsget_repo_variable  
  *description*: Gets a specific variable in a repository.  The authenticated user must have collaborator access to the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/variables_ 
  *resource*: actionslist_environment_variables  
  *description*: Lists all environment variables.  Authenticated users must have collaborator access to a repository to create, update, or read variables.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/variables/{name}_ 
  *resource*: actionsget_environment_variable  
  *description*: Gets a specific variable in an environment.  Authenticated users must have collaborator access to a repository to create, update, or read variables.  OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/permissions/access_ 
  *resource*: actionsget_workflow_access_to_repository  
  *description*: Gets the level of access that workflows outside of the repository have to actions and reusable workflows in the repository. This endpoint only applies to private repositories. For more information, see "[Allowing access to components in a private repository](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#allowing-access-to-components-in-a-private-repository)."  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/activity_ 
  *resource*: reposlist_activities  
  *description*: Lists a detailed history of changes to a repository, such as pushes, merges, force pushes, and branch changes, and associates these changes with commits and users.  For more information about viewing repository activity, see "[Viewing activity and data for your repository](https://docs.github.com/repositories/viewing-activity-and-data-for-your-repository)."
* _GET /app_ 
  *resource*: appsget_authenticated  
  *description*: Returns the GitHub App associated with the authentication credentials used. To see how many app installations are associated with this GitHub App, see the `installations_count` in the response. For more details about your app's installations, see the "[List installations for the authenticated app](https://docs.github.com/rest/apps/apps#list-installations-for-the-authenticated-app)" endpoint.  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /orgs/{org}/migrations/{migration_id}/archive_ 
  *resource*: migrationsdownload_archive_for_org  
  *description*: Fetches the URL to a migration archive.
* _GET /user/migrations/{migration_id}/archive_ 
  *resource*: migrationsget_archive_for_authenticated_user  
  *description*: Fetches the URL to download the migration archive as a `tar.gz` file. Depending on the resources your repository uses, the migration archive can contain JSON files with data for these objects:  *   attachments *   bases *   commit\_comments *   issue\_comments *   issue\_events *   issues *   milestones *   organizations *   projects *   protected\_branches *   pull\_request\_reviews *   pull\_requests *   releases *   repositories *   review\_comments *   schema *   users  The archive will also contain an `attachments` directory that includes all attachment files uploaded to GitHub.com and a `repositories` directory that contains the repository's Git data.
* _GET /repos/{owner}/{repo}/actions/artifacts_ 
  *resource*: actionslist_artifacts_for_repo  
  *description*: Lists all artifacts for a repository.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/actions/artifacts/{artifact_id}_ 
  *resource*: actionsget_artifact  
  *description*: Gets a specific artifact for a workflow run.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/artifacts/{artifact_id}/{archive_format}_ 
  *resource*: actionsdownload_artifact  
  *description*: Gets a redirect URL to download an archive for a repository. This URL expires after 1 minute. Look for `Location:` in the response header to find the URL for the download. The `:archive_format` must be `zip`.  OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts_ 
  *resource*: actionslist_workflow_run_artifacts  
  *description*: Lists artifacts for a workflow run.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/assignees/{assignee}_ 
  *resource*: issuescheck_user_can_be_assigned  
  *description*: Checks if a user has permission to be assigned to an issue in this repository.  If the `assignee` can be assigned to issues in the repository, a `204` header with no content is returned.  Otherwise a `404` status code is returned.
* _GET /repos/{owner}/{repo}/issues/{issue_number}/assignees/{assignee}_ 
  *resource*: issuescheck_user_can_be_assigned_to_issue  
  *description*: Checks if a user has permission to be assigned to a specific issue.  If the `assignee` can be assigned to this issue, a `204` status code with no content is returned.  Otherwise a `404` status code is returned.
* _GET /orgs/{org}/attestations/{subject_digest}_ 
  *resource*: orgslist_attestations  
  *description*: List a collection of artifact attestations with a given subject digest that are associated with repositories owned by an organization.  The collection of attestations returned by this endpoint is filtered according to the authenticated user's permissions; if the authenticated user cannot read a repository, the attestations associated with that repository will not be included in the response. In addition, when using a fine-grained access token the `attestations:read` permission is required.  **Please note:** in order to offer meaningful security benefits, an attestation's signature and timestamps **must** be cryptographically verified, and the identity of the attestation signer **must** be validated. Attestations can be verified using the [GitHub CLI `attestation verify` command](https://cli.github.com/manual/gh_attestation_verify). For more information, see [our guide on how to use artifact attestations to establish a build's provenance](https://docs.github.com/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds).
* _GET /repos/{owner}/{repo}/attestations/{subject_digest}_ 
  *resource*: reposlist_attestations  
  *description*: List a collection of artifact attestations with a given subject digest that are associated with a repository.  The authenticated user making the request must have read access to the repository. In addition, when using a fine-grained access token the `attestations:read` permission is required.  **Please note:** in order to offer meaningful security benefits, an attestation's signature and timestamps **must** be cryptographically verified, and the identity of the attestation signer **must** be validated. Attestations can be verified using the [GitHub CLI `attestation verify` command](https://cli.github.com/manual/gh_attestation_verify). For more information, see [our guide on how to use artifact attestations to establish a build's provenance](https://docs.github.com/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds).
* _GET /users/{username}/attestations/{subject_digest}_ 
  *resource*: userslist_attestations  
  *description*: List a collection of artifact attestations with a given subject digest that are associated with repositories owned by a user.  The collection of attestations returned by this endpoint is filtered according to the authenticated user's permissions; if the authenticated user cannot read a repository, the attestations associated with that repository will not be included in the response. In addition, when using a fine-grained access token the `attestations:read` permission is required.  **Please note:** in order to offer meaningful security benefits, an attestation's signature and timestamps **must** be cryptographically verified, and the identity of the attestation signer **must** be validated. Attestations can be verified using the [GitHub CLI `attestation verify` command](https://cli.github.com/manual/gh_attestation_verify). For more information, see [our guide on how to use artifact attestations to establish a build's provenance](https://docs.github.com/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds).
* _GET /repos/{owner}/{repo}/autolinks_ 
  *resource*: reposlist_autolinks  
  *description*: Gets all autolinks that are configured for a repository.  Information about autolinks are only available to repository administrators.
* _GET /repos/{owner}/{repo}/autolinks/{autolink_id}_ 
  *resource*: reposget_autolink  
  *description*: This returns a single autolink reference by ID that was configured for the given repository.  Information about autolinks are only available to repository administrators.
* _GET /gists_ 
  *resource*: gistslist  
  *description*: Lists the authenticated user's gists or if called anonymously, this endpoint returns all public gists:
* _GET /gists/public_ 
  *resource*: gistslist_public  
  *description*: List public gists sorted by most recently updated to least recently updated.  Note: With [pagination](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api), you can fetch up to 3000 gists. For example, you can fetch 100 pages with 30 gists per page or 30 pages with 100 gists per page.
* _GET /gists/starred_ 
  *resource*: gistslist_starred  
  *description*: List the authenticated user's starred gists:
* _GET /users/{username}/gists_ 
  *resource*: gistslist_for_user  
  *description*: Lists public gists for the specified user:
* _GET /repos/{owner}/{repo}/git/blobs/{file_sha}_ 
  *resource*: gitget_blob  
  *description*: The `content` in the response will always be Base64 encoded.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw blob data. - **`application/vnd.github+json`**: Returns a JSON representation of the blob with `content` as a base64 encoded string. This is the default if no media type is specified.  **Note** This endpoint supports blobs up to 100 megabytes in size.
* _GET /orgs/{org}/blocks/{username}_ 
  *resource*: orgscheck_blocked_user  
  *description*: Returns a 204 if the given user is blocked by the given organization. Returns a 404 if the organization is not blocking the user, or if the user account has been identified as spam by GitHub.
* _GET /user/blocks/{username}_ 
  *resource*: userscheck_blocked  
  *description*: Returns a 204 if the given user is blocked by the authenticated user. Returns a 404 if the given user is not blocked by the authenticated user, or if the given user account has been identified as spam by GitHub.
* _GET /repos/{owner}/{repo}/commits/{commit_sha}/branches-where-head_ 
  *resource*: reposlist_branches_for_head_commit  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.  Returns all branches where the given commit SHA is the HEAD, or latest commit for the branch.
* _GET /repos/{owner}/{repo}/branches/{branch}_ 
  *resource*: reposget_branch  
* _GET /repos/{owner}/{repo}/actions/caches_ 
  *resource*: actionsget_actions_cache_list  
  *description*: Lists the GitHub Actions caches for a repository.  OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/check-runs/{check_run_id}/annotations_ 
  *resource*: checkslist_annotations  
  *description*: Lists annotations for a check run using the annotation `id`.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint on a private repository.
* _GET /repos/{owner}/{repo}/automated-security-fixes_ 
  *resource*: reposcheck_automated_security_fixes  
  *description*: Shows whether automated security fixes are enabled, disabled or paused for a repository. The authenticated user must have admin read access to the repository. For more information, see "[Configuring automated security fixes](https://docs.github.com/articles/configuring-automated-security-fixes)".
* _GET /repos/{owner}/{repo}/check-runs/{check_run_id}_ 
  *resource*: checksget  
  *description*: Gets a single check run using its `id`.  > [!NOTE] > The Checks API only looks for pushes in the repository where the check suite or check run were created. Pushes to a branch in a forked repository are not detected and return an empty `pull_requests` array.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint on a private repository.
* _GET /repos/{owner}/{repo}/check-suites/{check_suite_id}/check-runs_ 
  *resource*: checkslist_for_suite  
  *description*: Lists check runs for a check suite using its `id`.  > [!NOTE] > The endpoints to manage checks only look for pushes in the repository where the check suite or check run were created. Pushes to a branch in a forked repository are not detected and return an empty `pull_requests` array.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint on a private repository.
* _GET /repos/{owner}/{repo}/commits/{ref}/check-runs_ 
  *resource*: checkslist_for_ref  
  *description*: Lists check runs for a commit ref. The `ref` can be a SHA, branch name, or a tag name.  > [!NOTE] > The endpoints to manage checks only look for pushes in the repository where the check suite or check run were created. Pushes to a branch in a forked repository are not detected and return an empty `pull_requests` array.  If there are more than 1000 check suites on a single git reference, this endpoint will limit check runs to the 1000 most recent check suites. To iterate over all possible check runs, use the [List check suites for a Git reference](https://docs.github.com/rest/reference/checks#list-check-suites-for-a-git-reference) endpoint and provide the `check_suite_id` parameter to the [List check runs in a check suite](https://docs.github.com/rest/reference/checks#list-check-runs-in-a-check-suite) endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint on a private repository.
* _GET /repos/{owner}/{repo}/check-suites/{check_suite_id}_ 
  *resource*: checksget_suite  
  *description*: Gets a single check suite using its `id`.  > [!NOTE] > The Checks API only looks for pushes in the repository where the check suite or check run were created. Pushes to a branch in a forked repository are not detected and return an empty `pull_requests` array and a `null` value for `head_branch`.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint on a private repository.
* _GET /repos/{owner}/{repo}/commits/{ref}/check-suites_ 
  *resource*: checkslist_suites_for_ref  
  *description*: Lists check suites for a commit `ref`. The `ref` can be a SHA, branch name, or a tag name.  > [!NOTE] > The endpoints to manage checks only look for pushes in the repository where the check suite or check run were created. Pushes to a branch in a forked repository are not detected and return an empty `pull_requests` array and a `null` value for `head_branch`.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint on a private repository.
* _GET /classrooms/{classroom_id}_ 
  *resource*: classroomget_a_classroom  
  *description*: Gets a GitHub Classroom classroom for the current user. Classroom will only be returned if the current user is an administrator of the GitHub Classroom.
* _GET /assignments/{assignment_id}/accepted_assignments_ 
  *resource*: classroomlist_accepted_assigments_for_an_assignment  
  *description*: Lists any assignment repositories that have been created by students accepting a GitHub Classroom assignment. Accepted assignments will only be returned if the current user is an administrator of the GitHub Classroom for the assignment.
* _GET /assignments/{assignment_id}_ 
  *resource*: classroomget_an_assignment  
  *description*: Gets a GitHub Classroom assignment. Assignment will only be returned if the current user is an administrator of the GitHub Classroom for the assignment.
* _GET /assignments/{assignment_id}/grades_ 
  *resource*: classroomget_assignment_grades  
  *description*: Gets grades for a GitHub Classroom assignment. Grades will only be returned if the current user is an administrator of the GitHub Classroom for the assignment.
* _GET /repos/{owner}/{repo}/stats/code_frequency_ 
  *resource*: reposget_code_frequency_stats  
  *description*: Returns a weekly aggregate of the number of additions and deletions pushed to a repository.  > [!NOTE] > This endpoint can only be used for repositories with fewer than 10,000 commits. If the repository contains 10,000 or more commits, a 422 status code will be returned.
* _GET /repos/{owner}/{repo}/stats/punch_card_ 
  *resource*: reposget_punch_card_stats  
  *description*: Each array contains the day number, hour number, and number of commits:  *   `0-6`: Sunday - Saturday *   `0-23`: Hour of day *   Number of commits  For example, `[2, 14, 25]` indicates that there were 25 total commits, during the 2:00pm hour on Tuesdays. All times are based on the time zone of individual commits.
* _GET /codes_of_conduct_ 
  *resource*: codes_of_conductget_all_codes_of_conduct  
  *description*: Returns array of all GitHub's codes of conduct.
* _GET /codes_of_conduct/{key}_ 
  *resource*: codes_of_conductget_conduct_code  
  *description*: Returns information about the specified GitHub code of conduct.
* _GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}_ 
  *resource*: code_scanningget_alert  
  *description*: Gets a single code scanning alert.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/alerts/{alert_number}/instances_ 
  *resource*: code_scanninglist_alert_instances  
  *description*: Lists all instances of the specified code scanning alert.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/alerts_ 
  *resource*: code_scanninglist_alerts_for_repo  
  *description*: Lists code scanning alerts.  The response includes a `most_recent_instance` object. This provides details of the most recent instance of this alert for the default branch (or for the specified Git reference if you used `ref` in the request).  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/analyses_ 
  *resource*: code_scanninglist_recent_analyses  
  *description*: Lists the details of all code scanning analyses for a repository, starting with the most recent. The response is paginated and you can use the `page` and `per_page` parameters to list the analyses you're interested in. By default 30 analyses are listed per page.  The `rules_count` field in the response give the number of rules that were run in the analysis. For very old analyses this data is not available, and `0` is returned in this field.  > [!WARNING] > **Deprecation notice:** The `tool_name` field is deprecated and will, in future, not be included in the response for this endpoint. The example response reflects this change. The tool name can now be found inside the `tool` field.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/analyses/{analysis_id}_ 
  *resource*: code_scanningget_analysis  
  *description*: Gets a specified code scanning analysis for a repository.  The default JSON response contains fields that describe the analysis. This includes the Git reference and commit SHA to which the analysis relates, the datetime of the analysis, the name of the code scanning tool, and the number of alerts.  The `rules_count` field in the default response give the number of rules that were run in the analysis. For very old analyses this data is not available, and `0` is returned in this field.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/sarif+json`**: Instead of returning a summary of the analysis, this endpoint returns a subset of the analysis data that was uploaded. The data is formatted as [SARIF version 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/cs01/sarif-v2.1.0-cs01.html). It also returns additional data such as the `github/alertNumber` and `github/alertUrl` properties.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/codeql/databases_ 
  *resource*: code_scanninglist_codeql_databases  
  *description*: Lists the CodeQL databases that are available in a repository.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/codeql/databases/{language}_ 
  *resource*: code_scanningget_codeql_database  
  *description*: Gets a CodeQL database for a language in a repository.  By default this endpoint returns JSON metadata about the CodeQL database. To download the CodeQL database binary content, set the `Accept` header of the request to [`application/zip`](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types), and make sure your HTTP client is configured to follow redirects or use the `Location` header to make a second request to get the redirect URL.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /orgs/{org}/code-scanning/alerts_ 
  *resource*: code_scanninglist_alerts_for_org  
  *description*: Lists code scanning alerts for the default branch for all eligible repositories in an organization. Eligible repositories are repositories that are owned by organizations that you own or for which you are a security manager. For more information, see "[Managing security managers in your organization](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization)."  The authenticated user must be an owner or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `security_events` or `repo`s cope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/sarifs/{sarif_id}_ 
  *resource*: code_scanningget_sarif  
  *description*: Gets information about a SARIF upload, including the status and the URL of the analysis that was uploaded so that you can retrieve details of the analysis. For more information, see "[Get a code scanning analysis for a repository](/rest/code-scanning/code-scanning#get-a-code-scanning-analysis-for-a-repository)." OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/codeql/variant-analyses/{codeql_variant_analysis_id}_ 
  *resource*: code_scanningget_variant_analysis  
  *description*: Gets the summary of a CodeQL variant analysis.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/code-scanning/codeql/variant-analyses/{codeql_variant_analysis_id}/repos/{repo_owner}/{repo_name}_ 
  *resource*: code_scanningget_variant_analysis_repo_task  
  *description*: Gets the analysis status of a repository in a CodeQL variant analysis.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /search/code_ 
  *resource*: searchcode  
  *description*: Searches for query terms inside of a file. This method returns up to 100 results [per page](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api).  When searching for code, you can get text match metadata for the file **content** and file **path** fields when you pass the `text-match` media type. For more details about how to receive highlighted search results, see [Text match metadata](https://docs.github.com/rest/search/search#text-match-metadata).  For example, if you want to find the definition of the `addClass` function inside [jQuery](https://github.com/jquery/jquery) repository, your query would look something like this:  `q=addClass+in:file+language:js+repo:jquery/jquery`  This query searches for the keyword `addClass` within a file's contents. The query limits the search to files where the language is JavaScript in the `jquery/jquery` repository.  Considerations for code search:  Due to the complexity of searching code, there are a few restrictions on how searches are performed:  *   Only the _default branch_ is considered. In most cases, this will be the `master` branch. *   Only files smaller than 384 KB are searchable. *   You must always include at least one search term when searching source code. For example, searching for [`language:go`](https://github.com/search?utf8=%E2%9C%93&q=language%3Ago&type=Code) is not valid, while [`amazing language:go`](https://github.com/search?utf8=%E2%9C%93&q=amazing+language%3Ago&type=Code) is.  This endpoint requires you to authenticate and limits you to 10 requests per minute.
* _GET /orgs/{org}/code-security/configurations_ 
  *resource*: code_securityget_configurations_for_org  
  *description*: Lists all code security configurations available in an organization.  The authenticated user must be an administrator or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `write:org` scope to use this endpoint.
* _GET /orgs/{org}/code-security/configurations/{configuration_id}_ 
  *resource*: code_securityget_configuration  
  *description*: Gets a code security configuration available in an organization.  The authenticated user must be an administrator or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `write:org` scope to use this endpoint.
* _GET /orgs/{org}/code-security/configurations/{configuration_id}/repositories_ 
  *resource*: code_securityget_repositories_for_configuration  
  *description*: Lists the repositories associated with a code security configuration in an organization.  The authenticated user must be an administrator or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `write:org` scope to use this endpoint.
* _GET /orgs/{org}/codespaces_ 
  *resource*: codespaceslist_in_organization  
  *description*: Lists the codespaces associated to a specified organization.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}/members/{username}/codespaces_ 
  *resource*: codespacesget_codespaces_for_user_in_org  
  *description*: Lists the codespaces that a member of an organization has for repositories in that organization.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/codespaces_ 
  *resource*: codespaceslist_in_repository_for_authenticated_user  
  *description*: Lists the codespaces associated to a specified repository and the authenticated user.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /user/codespaces_ 
  *resource*: codespaceslist_for_authenticated_user  
  *description*: Lists the authenticated user's codespaces.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /user/codespaces/{codespace_name}_ 
  *resource*: codespacesget_for_authenticated_user  
  *description*: Gets information about a user's codespace.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /user/codespaces/{codespace_name}/exports/{export_id}_ 
  *resource*: codespacesget_export_details_for_authenticated_user  
  *description*: Gets information about an export of a codespace.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/codespaces/machines_ 
  *resource*: codespacesrepo_machines_for_authenticated_user  
  *description*: List the machine types available for a given repository based on its configuration.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /user/codespaces/{codespace_name}/machines_ 
  *resource*: codespacescodespace_machines_for_authenticated_user  
  *description*: List the machine types a codespace can transition to use.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /orgs/{org}/codespaces/secrets_ 
  *resource*: codespaceslist_org_secrets  
  *description*: Lists all Codespaces development environment secrets available at the organization-level without revealing their encrypted values.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}/codespaces/secrets/{secret_name}_ 
  *resource*: codespacesget_org_secret  
  *description*: Gets an organization development environment secret without revealing its encrypted value.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/codespaces/permissions_check_ 
  *resource*: codespacescheck_permissions_for_devcontainer  
  *description*: Checks whether the permissions defined by a given devcontainer configuration have been accepted by the authenticated user.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /orgs/{org}/codespaces/secrets/public-key_ 
  *resource*: codespacesget_org_public_key  
  *description*: Gets a public key for an organization, which is required in order to encrypt secrets. You need to encrypt the value of a secret before you can create or update secrets. OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/codespaces/secrets/public-key_ 
  *resource*: codespacesget_repo_public_key  
  *description*: Gets your public key, which you need to encrypt secrets. You need to encrypt a secret before you can create or update secrets.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /user/codespaces/secrets_ 
  *resource*: codespaceslist_secrets_for_authenticated_user  
  *description*: Lists all development environment secrets available for a user's codespaces without revealing their encrypted values.  The authenticated user must have Codespaces access to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `codespace` or `codespace:secrets` scope to use this endpoint.
* _GET /user/codespaces/secrets/{secret_name}_ 
  *resource*: codespacesget_secret_for_authenticated_user  
  *description*: Gets a development environment secret available to a user's codespaces without revealing its encrypted value.  The authenticated user must have Codespaces access to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `codespace` or `codespace:secrets` scope to use this endpoint.
* _GET /user/codespaces/secrets/public-key_ 
  *resource*: codespacesget_public_key_for_authenticated_user  
  *description*: Gets your public key, which you need to encrypt secrets. You need to encrypt a secret before you can create or update secrets.  The authenticated user must have Codespaces access to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `codespace` or `codespace:secrets` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/collaborators_ 
  *resource*: reposlist_collaborators  
  *description*: For organization-owned repositories, the list of collaborators includes outside collaborators, organization members that are direct collaborators, organization members with access through team memberships, organization members with access through default organization permissions, and organization owners. Organization members with write, maintain, or admin privileges on the organization-owned repository can use this endpoint.  Team members will include the members of child teams.  The authenticated user must have push access to the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `read:org` and `repo` scopes to use this endpoint.
* _GET /repos/{owner}/{repo}/collaborators/{username}_ 
  *resource*: reposcheck_collaborator  
  *description*: For organization-owned repositories, the list of collaborators includes outside collaborators, organization members that are direct collaborators, organization members with access through team memberships, organization members with access through default organization permissions, and organization owners.  Team members will include the members of child teams.  The authenticated user must have push access to the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `read:org` and `repo` scopes to use this endpoint.
* _GET /orgs/{org}/settings/billing/shared-storage_ 
  *resource*: billingget_shared_storage_billing_org  
  *description*: Gets the estimated paid and estimated total storage used for GitHub Actions and GitHub Packages.  Paid minutes only apply to packages stored for private repositories. For more information, see "[Managing billing for GitHub Packages](https://docs.github.com/github/setting-up-and-managing-billing-and-payments-on-github/managing-billing-for-github-packages)."  OAuth app tokens and personal access tokens (classic) need the `repo` or `admin:org` scope to use this endpoint.
* _GET /users/{username}/settings/billing/shared-storage_ 
  *resource*: billingget_shared_storage_billing_user  
  *description*: Gets the estimated paid and estimated total storage used for GitHub Actions and GitHub Packages.  Paid minutes only apply to packages stored for private repositories. For more information, see "[Managing billing for GitHub Packages](https://docs.github.com/github/setting-up-and-managing-billing-and-payments-on-github/managing-billing-for-github-packages)."  OAuth app tokens and personal access tokens (classic) need the `user` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/commits_ 
  *resource*: reposlist_commits  
  *description*: **Signature verification object**  The response will include a `verification` object that describes the result of verifying the commit's signature. The following fields are included in the `verification` object:  | Name | Type | Description | | ---- | ---- | ----------- | | `verified` | `boolean` | Indicates whether GitHub considers the signature in this commit to be verified. | | `reason` | `string` | The reason for verified value. Possible values and their meanings are enumerated in table below. | | `signature` | `string` | The signature that was extracted from the commit. | | `payload` | `string` | The value that was signed. |  These are the possible values for `reason` in the `verification` object:  | Value | Description | | ----- | ----------- | | `expired_key` | The key that made the signature is expired. | | `not_signing_key` | The "signing" flag is not among the usage flags in the GPG key that made the signature. | | `gpgverify_error` | There was an error communicating with the signature verification service. | | `gpgverify_unavailable` | The signature verification service is currently unavailable. | | `unsigned` | The object does not include a signature. | | `unknown_signature_type` | A non-PGP signature was found in the commit. | | `no_user` | No user was associated with the `committer` email address in the commit. | | `unverified_email` | The `committer` email address in the commit was associated with a user, but the email address is not verified on their account. | | `bad_email` | The `committer` email address in the commit is not included in the identities of the PGP key that made the signature. | | `unknown_key` | The key that made the signature has not been registered with any user's account. | | `malformed_signature` | There was an error parsing the signature. | | `invalid` | The signature could not be cryptographically verified using the key whose key-id was found in the signature. | | `valid` | None of the above errors applied, so the signature is considered to be verified. |
* _GET /repos/{owner}/{repo}/commits/{ref}_ 
  *resource*: reposget_commit  
  *description*: Returns the contents of a single commit reference. You must have `read` access for the repository to use this endpoint.  > [!NOTE] > If there are more than 300 files in the commit diff and the default JSON media type is requested, the response will include pagination link headers for the remaining files, up to a limit of 3000 files. Each page contains the static commit information, and the only changes are to the file listing.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)." Pagination query parameters are not supported for these media types.  - **`application/vnd.github.diff`**: Returns the diff of the commit. Larger diffs may time out and return a 5xx status code. - **`application/vnd.github.patch`**: Returns the patch of the commit. Diffs with binary data will have no `patch` property. Larger diffs may time out and return a 5xx status code. - **`application/vnd.github.sha`**: Returns the commit's SHA-1 hash. You can use this endpoint to check if a remote reference's SHA-1 hash is the same as your local reference's SHA-1 hash by providing the local SHA-1 reference as the ETag.  **Signature verification object**  The response will include a `verification` object that describes the result of verifying the commit's signature. The following fields are included in the `verification` object:  | Name | Type | Description | | ---- | ---- | ----------- | | `verified` | `boolean` | Indicates whether GitHub considers the signature in this commit to be verified. | | `reason` | `string` | The reason for verified value. Possible values and their meanings are enumerated in table below. | | `signature` | `string` | The signature that was extracted from the commit. | | `payload` | `string` | The value that was signed. |  These are the possible values for `reason` in the `verification` object:  | Value | Description | | ----- | ----------- | | `expired_key` | The key that made the signature is expired. | | `not_signing_key` | The "signing" flag is not among the usage flags in the GPG key that made the signature. | | `gpgverify_error` | There was an error communicating with the signature verification service. | | `gpgverify_unavailable` | The signature verification service is currently unavailable. | | `unsigned` | The object does not include a signature. | | `unknown_signature_type` | A non-PGP signature was found in the commit. | | `no_user` | No user was associated with the `committer` email address in the commit. | | `unverified_email` | The `committer` email address in the commit was associated with a user, but the email address is not verified on their account. | | `bad_email` | The `committer` email address in the commit is not included in the identities of the PGP key that made the signature. | | `unknown_key` | The key that made the signature has not been registered with any user's account. | | `malformed_signature` | There was an error parsing the signature. | | `invalid` | The signature could not be cryptographically verified using the key whose key-id was found in the signature. | | `valid` | None of the above errors applied, so the signature is considered to be verified. |
* _GET /repos/{owner}/{repo}/compare/{basehead}_ 
  *resource*: reposcompare_commits  
  *description*: Compares two commits against one another. You can compare refs (branches or tags) and commit SHAs in the same repository, or you can compare refs and commit SHAs that exist in different repositories within the same repository network, including fork branches. For more information about how to view a repository's network, see "[Understanding connections between repositories](https://docs.github.com/repositories/viewing-activity-and-data-for-your-repository/understanding-connections-between-repositories)."  This endpoint is equivalent to running the `git log BASE..HEAD` command, but it returns commits in a different order. The `git log BASE..HEAD` command returns commits in reverse chronological order, whereas the API returns commits in chronological order.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.diff`**: Returns the diff of the commit. - **`application/vnd.github.patch`**: Returns the patch of the commit. Diffs with binary data will have no `patch` property.  The API response includes details about the files that were changed between the two commits. This includes the status of the change (if a file was added, removed, modified, or renamed), and details of the change itself. For example, files with a `renamed` status have a `previous_filename` field showing the previous filename of the file, and files with a `modified` status have a `patch` field showing the changes made to the file.  When calling this endpoint without any paging parameter (`per_page` or `page`), the returned list is limited to 250 commits, and the last commit in the list is the most recent of the entire comparison.  **Working with large comparisons**  To process a response with a large number of commits, use a query parameter (`per_page` or `page`) to paginate the results. When using pagination:  - The list of changed files is only shown on the first page of results, and it includes up to 300 changed files for the entire comparison. - The results are returned in chronological order, but the last commit in the returned list may not be the most recent one in the entire set if there are more pages of results.  For more information on working with pagination, see "[Using pagination in the REST API](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api)."  **Signature verification object**  The response will include a `verification` object that describes the result of verifying the commit's signature. The `verification` object includes the following fields:  | Name | Type | Description | | ---- | ---- | ----------- | | `verified` | `boolean` | Indicates whether GitHub considers the signature in this commit to be verified. | | `reason` | `string` | The reason for verified value. Possible values and their meanings are enumerated in table below. | | `signature` | `string` | The signature that was extracted from the commit. | | `payload` | `string` | The value that was signed. |  These are the possible values for `reason` in the `verification` object:  | Value | Description | | ----- | ----------- | | `expired_key` | The key that made the signature is expired. | | `not_signing_key` | The "signing" flag is not among the usage flags in the GPG key that made the signature. | | `gpgverify_error` | There was an error communicating with the signature verification service. | | `gpgverify_unavailable` | The signature verification service is currently unavailable. | | `unsigned` | The object does not include a signature. | | `unknown_signature_type` | A non-PGP signature was found in the commit. | | `no_user` | No user was associated with the `committer` email address in the commit. | | `unverified_email` | The `committer` email address in the commit was associated with a user, but the email address is not verified on their account. | | `bad_email` | The `committer` email address in the commit is not included in the identities of the PGP key that made the signature. | | `unknown_key` | The key that made the signature has not been registered with any user's account. | | `malformed_signature` | There was an error parsing the signature. | | `invalid` | The signature could not be cryptographically verified using the key whose key-id was found in the signature. | | `valid` | None of the above errors applied, so the signature is considered to be verified. |
* _GET /repos/{owner}/{repo}/pulls/{pull_number}/commits_ 
  *resource*: pullslist_commits  
  *description*: Lists a maximum of 250 commits for a pull request. To receive a complete commit list for pull requests with more than 250 commits, use the [List commits](https://docs.github.com/rest/commits/commits#list-commits) endpoint.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/stats/commit_activity_ 
  *resource*: reposget_commit_activity_stats  
  *description*: Returns the last year of commit activity grouped by week. The `days` array is a group of commits per day, starting on `Sunday`.
* _GET /repos/{owner}/{repo}/comments_ 
  *resource*: reposlist_commit_comments_for_repo  
  *description*: Lists the commit comments for a specified repository. Comments are ordered by ascending ID.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/comments/{comment_id}_ 
  *resource*: reposget_commit_comment  
  *description*: Gets a specified commit comment.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/commits/{commit_sha}/comments_ 
  *resource*: reposlist_comments_for_commit  
  *description*: Lists the comments for a specified commit.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /search/commits_ 
  *resource*: searchcommits  
  *description*: Find commits via various criteria on the default branch (usually `main`). This method returns up to 100 results [per page](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api).  When searching for commits, you can get text match metadata for the **message** field when you provide the `text-match` media type. For more details about how to receive highlighted search results, see [Text match metadata](https://docs.github.com/rest/search/search#text-match-metadata).  For example, if you want to find commits related to CSS in the [octocat/Spoon-Knife](https://github.com/octocat/Spoon-Knife) repository. Your query would look something like this:  `q=repo:octocat/Spoon-Knife+css`
* _GET /repos/{owner}/{repo}/community/profile_ 
  *resource*: reposget_community_profile_metrics  
  *description*: Returns all community profile metrics for a repository. The repository cannot be a fork.  The returned metrics include an overall health score, the repository description, the presence of documentation, the detected code of conduct, the detected license, and the presence of ISSUE\_TEMPLATE, PULL\_REQUEST\_TEMPLATE, README, and CONTRIBUTING files.  The `health_percentage` score is defined as a percentage of how many of the recommended community health files are present. For more information, see "[About community profiles for public repositories](https://docs.github.com/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories)."  `content_reports_enabled` is only returned for organization-owned repositories.
* _GET /repos/{owner}/{repo}/dependency-graph/compare/{basehead}_ 
  *resource*: dependency_graphdiff_range  
  *description*: Gets the diff of the dependency changes between two commits of a repository, based on the changes to the dependency manifests made in those commits.
* _GET /repos/{owner}/{repo}/contents/{path}_ 
  *resource*: reposget_content  
  *description*: Gets the contents of a file or directory in a repository. Specify the file path or directory with the `path` parameter. If you omit the `path` parameter, you will receive the contents of the repository's root directory.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw file contents for files and symlinks. - **`application/vnd.github.html+json`**: Returns the file contents in HTML. Markup languages are rendered to HTML using GitHub's open-source [Markup library](https://github.com/github/markup). - **`application/vnd.github.object+json`**: Returns the contents in a consistent object format regardless of the content type. For example, instead of an array of objects for a directory, the response will be an object with an `entries` attribute containing the array of objects.  If the content is a directory, the response will be an array of objects, one object for each item in the directory. When listing the contents of a directory, submodules have their "type" specified as "file". Logically, the value _should_ be "submodule". This behavior exists [for backwards compatibility purposes](https://git.io/v1YCW). In the next major version of the API, the type will be returned as "submodule".  If the content is a symlink and the symlink's target is a normal file in the repository, then the API responds with the content of the file. Otherwise, the API responds with an object describing the symlink itself.  If the content is a submodule, the `submodule_git_url` field identifies the location of the submodule repository, and the `sha` identifies a specific commit within the submodule repository. Git uses the given URL when cloning the submodule repository, and checks out the submodule at that specific commit. If the submodule repository is not hosted on github.com, the Git URLs (`git_url` and `_links["git"]`) and the github.com URLs (`html_url` and `_links["html"]`) will have null values.  **Notes**:  - To get a repository's contents recursively, you can [recursively get the tree](https://docs.github.com/rest/git/trees#get-a-tree). - This API has an upper limit of 1,000 files for a directory. If you need to retrieve more files, use the [Git Trees API](https://docs.github.com/rest/git/trees#get-a-tree). - Download URLs expire and are meant to be used just once. To ensure the download URL does not expire, please use the contents API to obtain a fresh download URL for each download. - If the requested file's size is:   - 1 MB or smaller: All features of this endpoint are supported.   - Between 1-100 MB: Only the `raw` or `object` custom media types are supported. Both will work as normal, except that when using the `object` media type, the `content` field will be an empty string and the `encoding` field will be `"none"`. To get the contents of these larger files, use the `raw` media type.   - Greater than 100 MB: This endpoint is not supported.
* _GET /repos/{owner}/{repo}/readme_ 
  *resource*: reposget_readme  
  *description*: Gets the preferred README for a repository.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw file contents. This is the default if you do not specify a media type. - **`application/vnd.github.html+json`**: Returns the README in HTML. Markup languages are rendered to HTML using GitHub's open-source [Markup library](https://github.com/github/markup).
* _GET /repos/{owner}/{repo}/readme/{dir}_ 
  *resource*: reposget_readme_in_directory  
  *description*: Gets the README from a repository directory.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw file contents. This is the default if you do not specify a media type. - **`application/vnd.github.html+json`**: Returns the README in HTML. Markup languages are rendered to HTML using GitHub's open-source [Markup library](https://github.com/github/markup).
* _GET /repos/{owner}/{repo}/traffic/popular/paths_ 
  *resource*: reposget_top_paths  
  *description*: Get the top 10 popular contents over the last 14 days.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks/contexts_ 
  *resource*: reposget_all_status_check_contexts  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.
* _GET /repos/{owner}/{repo}/contributors_ 
  *resource*: reposlist_contributors  
  *description*: Lists contributors to the specified repository and sorts them by the number of commits per contributor in descending order. This endpoint may return information that is a few hours old because the GitHub REST API caches contributor data to improve performance.  GitHub identifies contributors by author email address. This endpoint groups contribution counts by GitHub user, which includes all associated email addresses. To improve performance, only the first 500 author email addresses in the repository link to GitHub users. The rest will appear as anonymous contributors without associated GitHub user information.
* _GET /repos/{owner}/{repo}/stats/contributors_ 
  *resource*: reposget_contributors_stats  
  *description*:  Returns the `total` number of commits authored by the contributor. In addition, the response includes a Weekly Hash (`weeks` array) with the following information:  *   `w` - Start of the week, given as a [Unix timestamp](https://en.wikipedia.org/wiki/Unix_time). *   `a` - Number of additions *   `d` - Number of deletions *   `c` - Number of commits  > [!NOTE] > This endpoint will return `0` values for all addition and deletion counts in repositories with 10,000 or more commits.
* _GET /orgs/{org}/copilot/billing_ 
  *resource*: copilotget_copilot_organization_details  
  *description*: > [!NOTE] > This endpoint is in beta and is subject to change.  Gets information about an organization's Copilot subscription, including seat breakdown and feature policies. To configure these settings, go to your organization's settings on GitHub.com. For more information, see "[Managing policies for Copilot in your organization](https://docs.github.com/copilot/managing-copilot/managing-policies-for-copilot-business-in-your-organization)".  Only organization owners can view details about the organization's Copilot Business or Copilot Enterprise subscription.  OAuth app tokens and personal access tokens (classic) need either the `manage_billing:copilot` or `read:org` scopes to use this endpoint.
* _GET /enterprises/{enterprise}/copilot/billing/seats_ 
  *resource*: copilotlist_copilot_seats_for_enterprise  
  *description*: > [!NOTE] > This endpoint is in beta and is subject to change.  Lists all active Copilot seats across organizations or enterprise teams for an enterprise with a Copilot Business or Copilot Enterprise subscription.  Users with access through multiple organizations or enterprise teams will only be counted toward `total_seats` once.  For each organization or enterprise team which grants Copilot access to a user, a seat detail object will appear in the `seats` array.  Only enterprise owners and billing managers can view assigned Copilot seats across their child organizations or enterprise teams.  Personal access tokens (classic) need either the `manage_billing:copilot` or `read:enterprise` scopes to use this endpoint.
* _GET /orgs/{org}/copilot/billing/seats_ 
  *resource*: copilotlist_copilot_seats  
  *description*: > [!NOTE] > This endpoint is in beta and is subject to change.  Lists all active Copilot seats for an organization with a Copilot Business or Copilot Enterprise subscription. Only organization owners can view assigned seats.  OAuth app tokens and personal access tokens (classic) need either the `manage_billing:copilot` or `read:org` scopes to use this endpoint.
* _GET /orgs/{org}/members/{username}/copilot_ 
  *resource*: copilotget_copilot_seat_details_for_user  
  *description*: > [!NOTE] > This endpoint is in beta and is subject to change.  Gets the GitHub Copilot seat assignment details for a member of an organization who currently has access to GitHub Copilot.  Only organization owners can view Copilot seat assignment details for members of their organization.  OAuth app tokens and personal access tokens (classic) need either the `manage_billing:copilot` or `read:org` scopes to use this endpoint.
* _GET /enterprises/{enterprise}/copilot/usage_ 
  *resource*: copilotusage_metrics_for_enterprise  
  *description*: > [!NOTE] > This endpoint is in beta and is subject to change.  You can use this endpoint to see a daily breakdown of aggregated usage metrics for Copilot completions and Copilot Chat in the IDE for all users across organizations with access to Copilot within your enterprise, with a further breakdown of suggestions, acceptances, and number of active users by editor and language for each day. See the response schema tab for detailed metrics definitions.  The response contains metrics for the prior 28 days. Usage metrics are processed once per day for the previous day, and the response will only include data up until yesterday. In order for an end user to be counted towards these metrics, they must have telemetry enabled in their IDE.  Only owners and billing managers can view Copilot usage metrics for the enterprise.  OAuth app tokens and personal access tokens (classic) need either the `manage_billing:copilot` or `read:enterprise` scopes to use this endpoint.
* _GET /orgs/{org}/copilot/usage_ 
  *resource*: copilotusage_metrics_for_org  
  *description*: > [!NOTE] > This endpoint is in beta and is subject to change.  You can use this endpoint to see a daily breakdown of aggregated usage metrics for Copilot completions and Copilot Chat in the IDE across an organization, with a further breakdown of suggestions, acceptances, and number of active users by editor and language for each day. See the response schema tab for detailed metrics definitions.  The response contains metrics for the prior 28 days. Usage metrics are processed once per day for the previous day, and the response will only include data up until yesterday. In order for an end user to be counted towards these metrics, they must have telemetry enabled in their IDE.  Organization owners, and owners and billing managers of the parent enterprise, can view Copilot usage metrics.  OAuth app tokens and personal access tokens (classic) need either the `manage_billing:copilot`, `read:org`, or `read:enterprise` scopes to use this endpoint.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules/apps_ 
  *resource*: reposlist_custom_deployment_rule_integrations  
  *description*: Gets all custom deployment protection rule integrations that are available for an environment.  The authenticated user must have admin or owner permissions to the repository to use this endpoint.  For more information about environments, see "[Using environments for deployment](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)."  For more information about the app that is providing this custom deployment rule, see "[GET an app](https://docs.github.com/rest/apps/apps#get-an-app)".  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/properties/values_ 
  *resource*: reposget_custom_properties_values  
  *description*: Gets all custom property values that are set for a repository. Users with read access to the repository can use this endpoint.
* _GET /orgs/{org}/code-security/configurations/defaults_ 
  *resource*: code_securityget_default_configurations  
  *description*: Lists the default code security configurations for an organization.  The authenticated user must be an administrator or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `write:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/code-scanning/default-setup_ 
  *resource*: code_scanningget_default_setup  
  *description*: Gets a code scanning default setup configuration.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with private or public repositories, or the `public_repo` scope to use this endpoint with only public repositories.
* _GET /repos/{owner}/{repo}/dependabot/alerts_ 
  *resource*: dependabotlist_alerts_for_repo  
  *description*: OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint. If this endpoint is only used with public repositories, the token can use the `public_repo` scope instead.
* _GET /repos/{owner}/{repo}/dependabot/alerts/{alert_number}_ 
  *resource*: dependabotget_alert  
  *description*: OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint. If this endpoint is only used with public repositories, the token can use the `public_repo` scope instead.
* _GET /enterprises/{enterprise}/dependabot/alerts_ 
  *resource*: dependabotlist_alerts_for_enterprise  
  *description*: Lists Dependabot alerts for repositories that are owned by the specified enterprise.  The authenticated user must be a member of the enterprise to use this endpoint.  Alerts are only returned for organizations in the enterprise for which you are an organization owner or a security manager. For more information about security managers, see "[Managing security managers in your organization](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization)."  OAuth app tokens and personal access tokens (classic) need the `repo` or `security_events` scope to use this endpoint.
* _GET /orgs/{org}/dependabot/alerts_ 
  *resource*: dependabotlist_alerts_for_org  
  *description*: Lists Dependabot alerts for an organization.  The authenticated user must be an owner or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `security_events` scope to use this endpoint. If this endpoint is only used with public repositories, the token can use the `public_repo` scope instead.
* _GET /orgs/{org}/dependabot/secrets/public-key_ 
  *resource*: dependabotget_org_public_key  
  *description*: Gets your public key, which you need to encrypt secrets. You need to encrypt a secret before you can create or update secrets.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/dependabot/secrets/public-key_ 
  *resource*: dependabotget_repo_public_key  
  *description*: Gets your public key, which you need to encrypt secrets. You need to encrypt a secret before you can create or update secrets. Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint if the repository is private.
* _GET /repos/{owner}/{repo}/dependabot/secrets_ 
  *resource*: dependabotlist_repo_secrets  
  *description*: Lists all secrets available in a repository without revealing their encrypted values.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/dependabot/secrets/{secret_name}_ 
  *resource*: dependabotget_repo_secret  
  *description*: Gets a single repository secret without revealing its encrypted value.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/keys_ 
  *resource*: reposlist_deploy_keys  
* _GET /repos/{owner}/{repo}/keys/{key_id}_ 
  *resource*: reposget_deploy_key  
* _GET /repos/{owner}/{repo}/deployments_ 
  *resource*: reposlist_deployments  
  *description*: Simple filtering of deployments is available via query parameters:
* _GET /repos/{owner}/{repo}/deployments/{deployment_id}_ 
  *resource*: reposget_deployment  
* _GET /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies_ 
  *resource*: reposlist_deployment_branch_policies  
  *description*: Lists the deployment branch policies for an environment.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies/{branch_policy_id}_ 
  *resource*: reposget_deployment_branch_policy  
  *description*: Gets a deployment branch or tag policy for an environment.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules_ 
  *resource*: reposget_all_deployment_protection_rules  
  *description*: Gets all custom deployment protection rules that are enabled for an environment. Anyone with read access to the repository can use this endpoint. For more information about environments, see "[Using environments for deployment](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)."  For more information about the app that is providing this custom deployment rule, see the [documentation for the `GET /apps/{app_slug}` endpoint](https://docs.github.com/rest/apps/apps#get-an-app).  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules/{protection_rule_id}_ 
  *resource*: reposget_custom_deployment_protection_rule  
  *description*: Gets an enabled custom deployment protection rule for an environment. Anyone with read access to the repository can use this endpoint. For more information about environments, see "[Using environments for deployment](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)."  For more information about the app that is providing this custom deployment rule, see [`GET /apps/{app_slug}`](https://docs.github.com/rest/apps/apps#get-an-app).  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/deployments/{deployment_id}/statuses_ 
  *resource*: reposlist_deployment_statuses  
  *description*: Users with pull access can view deployment statuses for a deployment:
* _GET /repos/{owner}/{repo}/deployments/{deployment_id}/statuses/{status_id}_ 
  *resource*: reposget_deployment_status  
  *description*: Users with pull access can view a deployment status for a deployment:
* _GET /repos/{owner}/{repo}/codespaces/devcontainers_ 
  *resource*: codespaceslist_devcontainers_in_repository_for_authenticated_user  
  *description*: Lists the devcontainer.json files associated with a specified repository and the authenticated user. These files specify launchpoint configurations for codespaces created within the repository.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/pulls/{pull_number}/files_ 
  *resource*: pullslist_files  
  *description*: Lists the files in a specified pull request.  > [!NOTE] > Responses include a maximum of 3000 files. The paginated response returns 30 files per page by default.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /user/emails_ 
  *resource*: userslist_emails_for_authenticated_user  
  *description*: Lists all of your email addresses, and specifies which one is visible to the public.  OAuth app tokens and personal access tokens (classic) need the `user:email` scope to use this endpoint.
* _GET /user/public_emails_ 
  *resource*: userslist_public_emails_for_authenticated_user  
  *description*: Lists your publicly visible email address, which you can set with the [Set primary email visibility for the authenticated user](https://docs.github.com/rest/users/emails#set-primary-email-visibility-for-the-authenticated-user) endpoint.  OAuth app tokens and personal access tokens (classic) need the `user:email` scope to use this endpoint.
* _GET /emojis_ 
  *resource*: emojisget  
  *description*: Lists all the emojis available to use on GitHub.
* _GET /repos/{owner}/{repo}/environments_ 
  *resource*: reposget_all_environments  
  *description*: Lists the environments for a repository.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/environments/{environment_name}_ 
  *resource*: reposget_environment  
  *description*: > [!NOTE] > To get information about name patterns that branches must match in order to deploy to this environment, see "[Get a deployment branch policy](/rest/deployments/branch-policies#get-a-deployment-branch-policy)."  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/approvals_ 
  *resource*: actionsget_reviews_for_run  
  *description*: Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/codeowners/errors_ 
  *resource*: reposcodeowners_errors  
  *description*: List any syntax errors that are detected in the CODEOWNERS file.  For more information about the correct CODEOWNERS syntax, see "[About code owners](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)."
* _GET /events_ 
  *resource*: activitylist_public_events  
  *description*: We delay the public events feed by five minutes, which means the most recent event returned by the public events API actually occurred at least five minutes ago.
* _GET /networks/{owner}/{repo}/events_ 
  *resource*: activitylist_public_events_for_repo_network  
* _GET /orgs/{org}/events_ 
  *resource*: activitylist_public_org_events  
* _GET /repos/{owner}/{repo}/events_ 
  *resource*: activitylist_repo_events  
  *description*: > [!NOTE] > This API is not built to serve real-time use cases. Depending on the time of day, event latency can be anywhere from 30s to 6h.
* _GET /users/{username}/events_ 
  *resource*: activitylist_events_for_authenticated_user  
  *description*: If you are authenticated as the given user, you will see your private events. Otherwise, you'll only see public events.
* _GET /users/{username}/events/orgs/{org}_ 
  *resource*: activitylist_org_events_for_authenticated_user  
  *description*: This is the user's organization dashboard. You must be authenticated as the user to view this.
* _GET /users/{username}/events/public_ 
  *resource*: activitylist_public_events_for_user  
* _GET /users/{username}/received_events_ 
  *resource*: activitylist_received_events_for_user  
  *description*: These are events that you've received by watching repositories and following users. If you are authenticated as the given user, you will see private events. Otherwise, you'll only see public events.
* _GET /users/{username}/received_events/public_ 
  *resource*: activitylist_received_public_events_for_user  
* _GET /feeds_ 
  *resource*: activityget_feeds  
  *description*: Lists the feeds available to the authenticated user. The response provides a URL for each feed. You can then get a specific feed by sending a request to one of the feed URLs.  *   **Timeline**: The GitHub global public timeline *   **User**: The public timeline for any user, using `uri_template`. For more information, see "[Hypermedia](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#hypermedia)." *   **Current user public**: The public timeline for the authenticated user *   **Current user**: The private timeline for the authenticated user *   **Current user actor**: The private timeline for activity created by the authenticated user *   **Current user organizations**: The private timeline for the organizations the authenticated user is a member of. *   **Security advisories**: A collection of public announcements that provide information about security-related vulnerabilities in software on GitHub.  By default, timeline resources are returned in JSON. You can specify the `application/atom+xml` type in the `Accept` header to return timeline resources in Atom format. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  > [!NOTE] > Private feeds are only returned when [authenticating via Basic Auth](https://docs.github.com/rest/authentication/authenticating-to-the-rest-api#using-basic-authentication) since current feed URIs use the older, non revocable auth tokens.
* _GET /user/following/{username}_ 
  *resource*: userscheck_person_is_followed_by_authenticated  
* _GET /users/{username}/following/{target_user}_ 
  *resource*: userscheck_following_for_user  
* _GET /repos/{owner}/{repo}_ 
  *resource*: reposget  
  *description*: The `parent` and `source` objects are present when the repository is a fork. `parent` is the repository this repository was forked from, `source` is the ultimate source for the network.  > [!NOTE] > In order to see the `security_and_analysis` block for a repository you must have admin permissions for the repository or be an owner or security manager for the organization that owns the repository. For more information, see "[Managing security managers in your organization](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization)."
* _GET /gists/{gist_id}/comments_ 
  *resource*: gistslist_comments  
  *description*: Lists the comments on a gist.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown. This is the default if you do not pass any specific media type. - **`application/vnd.github.base64+json`**: Returns the base64-encoded contents. This can be useful if your gist contains any invalid UTF-8 sequences.
* _GET /gists/{gist_id}/comments/{comment_id}_ 
  *resource*: gistsget_comment  
  *description*: Gets a comment on a gist.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown. This is the default if you do not pass any specific media type. - **`application/vnd.github.base64+json`**: Returns the base64-encoded contents. This can be useful if your gist contains any invalid UTF-8 sequences.
* _GET /gists/{gist_id}/commits_ 
  *resource*: gistslist_commits  
* _GET /gists/{gist_id}_ 
  *resource*: gistsget  
  *description*: Gets a specified gist.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown. This is the default if you do not pass any specific media type. - **`application/vnd.github.base64+json`**: Returns the base64-encoded contents. This can be useful if your gist contains any invalid UTF-8 sequences.
* _GET /gists/{gist_id}/forks_ 
  *resource*: gistslist_forks  
* _GET /gists/{gist_id}/{sha}_ 
  *resource*: gistsget_revision  
  *description*: Gets a specified gist revision.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown. This is the default if you do not pass any specific media type. - **`application/vnd.github.base64+json`**: Returns the base64-encoded contents. This can be useful if your gist contains any invalid UTF-8 sequences.
* _GET /repos/{owner}/{repo}/git/commits/{commit_sha}_ 
  *resource*: gitget_commit  
  *description*: Gets a Git [commit object](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects).  To get the contents of a commit, see "[Get a commit](/rest/commits/commits#get-a-commit)."  **Signature verification object**  The response will include a `verification` object that describes the result of verifying the commit's signature. The following fields are included in the `verification` object:  | Name | Type | Description | | ---- | ---- | ----------- | | `verified` | `boolean` | Indicates whether GitHub considers the signature in this commit to be verified. | | `reason` | `string` | The reason for verified value. Possible values and their meanings are enumerated in the table below. | | `signature` | `string` | The signature that was extracted from the commit. | | `payload` | `string` | The value that was signed. |  These are the possible values for `reason` in the `verification` object:  | Value | Description | | ----- | ----------- | | `expired_key` | The key that made the signature is expired. | | `not_signing_key` | The "signing" flag is not among the usage flags in the GPG key that made the signature. | | `gpgverify_error` | There was an error communicating with the signature verification service. | | `gpgverify_unavailable` | The signature verification service is currently unavailable. | | `unsigned` | The object does not include a signature. | | `unknown_signature_type` | A non-PGP signature was found in the commit. | | `no_user` | No user was associated with the `committer` email address in the commit. | | `unverified_email` | The `committer` email address in the commit was associated with a user, but the email address is not verified on their account. | | `bad_email` | The `committer` email address in the commit is not included in the identities of the PGP key that made the signature. | | `unknown_key` | The key that made the signature has not been registered with any user's account. | | `malformed_signature` | There was an error parsing the signature. | | `invalid` | The signature could not be cryptographically verified using the key whose key-id was found in the signature. | | `valid` | None of the above errors applied, so the signature is considered to be verified. |
* _GET /repos/{owner}/{repo}/git/matching-refs/{ref}_ 
  *resource*: gitlist_matching_refs  
  *description*: Returns an array of references from your Git database that match the supplied name. The `:ref` in the URL must be formatted as `heads/<branch name>` for branches and `tags/<tag name>` for tags. If the `:ref` doesn't exist in the repository, but existing refs start with `:ref`, they will be returned as an array.  When you use this endpoint without providing a `:ref`, it will return an array of all the references from your Git database, including notes and stashes if they exist on the server. Anything in the namespace is returned, not just `heads` and `tags`.  > [!NOTE] > You need to explicitly [request a pull request](https://docs.github.com/rest/pulls/pulls#get-a-pull-request) to trigger a test merge commit, which checks the mergeability of pull requests. For more information, see "[Checking mergeability of pull requests](https://docs.github.com/rest/guides/getting-started-with-the-git-database-api#checking-mergeability-of-pull-requests)".  If you request matching references for a branch named `feature` but the branch `feature` doesn't exist, the response can still include other matching head refs that start with the word `feature`, such as `featureA` and `featureB`.
* _GET /repos/{owner}/{repo}/git/ref/{ref}_ 
  *resource*: gitget_ref  
  *description*: Returns a single reference from your Git database. The `:ref` in the URL must be formatted as `heads/<branch name>` for branches and `tags/<tag name>` for tags. If the `:ref` doesn't match an existing ref, a `404` is returned.  > [!NOTE] > You need to explicitly [request a pull request](https://docs.github.com/rest/pulls/pulls#get-a-pull-request) to trigger a test merge commit, which checks the mergeability of pull requests. For more information, see "[Checking mergeability of pull requests](https://docs.github.com/rest/guides/getting-started-with-the-git-database-api#checking-mergeability-of-pull-requests)".
* _GET /repos/{owner}/{repo}/git/tags/{tag_sha}_ 
  *resource*: gitget_tag  
  *description*: **Signature verification object**  The response will include a `verification` object that describes the result of verifying the commit's signature. The following fields are included in the `verification` object:  | Name | Type | Description | | ---- | ---- | ----------- | | `verified` | `boolean` | Indicates whether GitHub considers the signature in this commit to be verified. | | `reason` | `string` | The reason for verified value. Possible values and their meanings are enumerated in table below. | | `signature` | `string` | The signature that was extracted from the commit. | | `payload` | `string` | The value that was signed. |  These are the possible values for `reason` in the `verification` object:  | Value | Description | | ----- | ----------- | | `expired_key` | The key that made the signature is expired. | | `not_signing_key` | The "signing" flag is not among the usage flags in the GPG key that made the signature. | | `gpgverify_error` | There was an error communicating with the signature verification service. | | `gpgverify_unavailable` | The signature verification service is currently unavailable. | | `unsigned` | The object does not include a signature. | | `unknown_signature_type` | A non-PGP signature was found in the commit. | | `no_user` | No user was associated with the `committer` email address in the commit. | | `unverified_email` | The `committer` email address in the commit was associated with a user, but the email address is not verified on their account. | | `bad_email` | The `committer` email address in the commit is not included in the identities of the PGP key that made the signature. | | `unknown_key` | The key that made the signature has not been registered with any user's account. | | `malformed_signature` | There was an error parsing the signature. | | `invalid` | The signature could not be cryptographically verified using the key whose key-id was found in the signature. | | `valid` | None of the above errors applied, so the signature is considered to be verified. |
* _GET /repos/{owner}/{repo}/git/trees/{tree_sha}_ 
  *resource*: gitget_tree  
  *description*: Returns a single tree using the SHA1 value or ref name for that tree.  If `truncated` is `true` in the response then the number of items in the `tree` array exceeded our maximum limit. If you need to fetch more items, use the non-recursive method of fetching trees, and fetch one sub-tree at a time.  > [!NOTE] > The limit for the `tree` array is 100,000 entries with a maximum size of 7 MB when using the `recursive` parameter.
* _GET /gitignore/templates/{name}_ 
  *resource*: gitignoreget_template  
  *description*: Get the content of a gitignore template.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw .gitignore contents.
* _GET /advisories_ 
  *resource*: security_advisorieslist_global_advisories  
  *description*: Lists all global security advisories that match the specified parameters. If no other parameters are defined, the request will return only GitHub-reviewed advisories that are not malware.  By default, all responses will exclude advisories for malware, because malware are not standard vulnerabilities. To list advisories for malware, you must include the `type` parameter in your request, with the value `malware`. For more information about the different types of security advisories, see "[About the GitHub Advisory database](https://docs.github.com/code-security/security-advisories/global-security-advisories/about-the-github-advisory-database#about-types-of-security-advisories)."
* _GET /advisories/{ghsa_id}_ 
  *resource*: security_advisoriesget_global_advisory  
  *description*: Gets a global security advisory using its GitHub Security Advisory (GHSA) identifier.
* _GET /user/gpg_keys_ 
  *resource*: userslist_gpg_keys_for_authenticated_user  
  *description*: Lists the current user's GPG keys.  OAuth app tokens and personal access tokens (classic) need the `read:gpg_key` scope to use this endpoint.
* _GET /user/gpg_keys/{gpg_key_id}_ 
  *resource*: usersget_gpg_key_for_authenticated_user  
  *description*: View extended details for a single GPG key.  OAuth app tokens and personal access tokens (classic) need the `read:gpg_key` scope to use this endpoint.
* _GET /users/{username}/gpg_keys_ 
  *resource*: userslist_gpg_keys_for_user  
  *description*: Lists the GPG keys for a user. This information is accessible by anyone.
* _GET /repos/{owner}/{repo}/hooks_ 
  *resource*: reposlist_webhooks  
  *description*: Lists webhooks for a repository. `last response` may return null if there have not been any deliveries within 30 days.
* _GET /repos/{owner}/{repo}/hooks/{hook_id}_ 
  *resource*: reposget_webhook  
  *description*: Returns a webhook configured in a repository. To get only the webhook `config` properties, see "[Get a webhook configuration for a repository](/rest/webhooks/repo-config#get-a-webhook-configuration-for-a-repository)."
* _GET /app/hook/deliveries/{delivery_id}_ 
  *resource*: appsget_webhook_delivery  
  *description*: Returns a delivery for the webhook configured for a GitHub App.  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /orgs/{org}/hooks/{hook_id}/deliveries/{delivery_id}_ 
  *resource*: orgsget_webhook_delivery  
  *description*: Returns a delivery for a webhook configured in an organization.  You must be an organization owner to use this endpoint.  OAuth app tokens and personal access tokens (classic) need `admin:org_hook` scope. OAuth apps cannot list, view, or edit webhooks that they did not create and users cannot list, view, or edit webhooks that were created by OAuth apps.
* _GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}_ 
  *resource*: reposget_webhook_delivery  
  *description*: Returns a delivery for a webhook configured in a repository.
* _GET /app/hook/deliveries_ 
  *resource*: appslist_webhook_deliveries  
  *description*: Returns a list of webhook deliveries for the webhook configured for a GitHub App.  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /orgs/{org}/hooks/{hook_id}/deliveries_ 
  *resource*: orgslist_webhook_deliveries  
  *description*: Returns a list of webhook deliveries for a webhook configured in an organization.  You must be an organization owner to use this endpoint.  OAuth app tokens and personal access tokens (classic) need `admin:org_hook` scope. OAuth apps cannot list, view, or edit webhooks that they did not create and users cannot list, view, or edit webhooks that were created by OAuth apps.
* _GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries_ 
  *resource*: reposlist_webhook_deliveries  
  *description*: Returns a list of webhook deliveries for a webhook configured in a repository.
* _GET /users/{username}/hovercard_ 
  *resource*: usersget_context_for_user  
  *description*: Provides hovercard information. You can find out more about someone in relation to their pull requests, issues, repositories, and organizations.    The `subject_type` and `subject_id` parameters provide context for the person's hovercard, which returns more information than without the parameters. For example, if you wanted to find out more about `octocat` who owns the `Spoon-Knife` repository, you would use a `subject_type` value of `repository` and a `subject_id` value of `1300192` (the ID of the `Spoon-Knife` repository).  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/import_ 
  *resource*: migrationsget_import_status  
  *description*: View the progress of an import.  > [!WARNING] > **Deprecation notice:** Due to very low levels of usage and available alternatives, this endpoint is deprecated and will no longer be available from 00:00 UTC on April 12, 2024. For more details and alternatives, see the [changelog](https://gh.io/source-imports-api-deprecation).  **Import status**  This section includes details about the possible values of the `status` field of the Import Progress response.  An import that does not have errors will progress through these steps:  *   `detecting` - the "detection" step of the import is in progress because the request did not include a `vcs` parameter. The import is identifying the type of source control present at the URL. *   `importing` - the "raw" step of the import is in progress. This is where commit data is fetched from the original repository. The import progress response will include `commit_count` (the total number of raw commits that will be imported) and `percent` (0 - 100, the current progress through the import). *   `mapping` - the "rewrite" step of the import is in progress. This is where SVN branches are converted to Git branches, and where author updates are applied. The import progress response does not include progress information. *   `pushing` - the "push" step of the import is in progress. This is where the importer updates the repository on GitHub. The import progress response will include `push_percent`, which is the percent value reported by `git push` when it is "Writing objects". *   `complete` - the import is complete, and the repository is ready on GitHub.  If there are problems, you will see one of these in the `status` field:  *   `auth_failed` - the import requires authentication in order to connect to the original repository. To update authentication for the import, please see the [Update an import](https://docs.github.com/rest/migrations/source-imports#update-an-import) section. *   `error` - the import encountered an error. The import progress response will include the `failed_step` and an error message. Contact [GitHub Support](https://support.github.com/contact?tags=dotcom-rest-api) for more information. *   `detection_needs_auth` - the importer requires authentication for the originating repository to continue detection. To update authentication for the import, please see the [Update an import](https://docs.github.com/rest/migrations/source-imports#update-an-import) section. *   `detection_found_nothing` - the importer didn't recognize any source control at the URL. To resolve, [Cancel the import](https://docs.github.com/rest/migrations/source-imports#cancel-an-import) and [retry](https://docs.github.com/rest/migrations/source-imports#start-an-import) with the correct URL. *   `detection_found_multiple` - the importer found several projects or repositories at the provided URL. When this is the case, the Import Progress response will also include a `project_choices` field with the possible project choices as values. To update project choice, please see the [Update an import](https://docs.github.com/rest/migrations/source-imports#update-an-import) section.  **The project_choices field**  When multiple projects are found at the provided URL, the response hash will include a `project_choices` field, the value of which is an array of hashes each representing a project choice. The exact key/value pairs of the project hashes will differ depending on the version control type.  **Git LFS related fields**  This section includes details about Git LFS related fields that may be present in the Import Progress response.  *   `use_lfs` - describes whether the import has been opted in or out of using Git LFS. The value can be `opt_in`, `opt_out`, or `undecided` if no action has been taken. *   `has_large_files` - the boolean value describing whether files larger than 100MB were found during the `importing` step. *   `large_files_size` - the total size in gigabytes of files larger than 100MB found in the originating repository. *   `large_files_count` - the total number of files larger than 100MB found in the originating repository. To see a list of these files, make a "Get Large Files" request.
* _GET /app/installations_ 
  *resource*: appslist_installations  
  *description*: The permissions the installation has are included under the `permissions` key.  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /app/installations/{installation_id}_ 
  *resource*: appsget_installation  
  *description*: Enables an authenticated GitHub App to find an installation's information using the installation id.  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /orgs/{org}/installation_ 
  *resource*: appsget_org_installation  
  *description*: Enables an authenticated GitHub App to find the organization's installation information.  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /orgs/{org}/installations_ 
  *resource*: orgslist_app_installations  
  *description*: Lists all GitHub Apps in an organization. The installation count includes all GitHub Apps installed on repositories in the organization.  The authenticated user must be an organization owner to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `admin:read` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/installation_ 
  *resource*: appsget_repo_installation  
  *description*: Enables an authenticated GitHub App to find the repository's installation information. The installation's account type will be either an organization or a user account, depending which account the repository belongs to.  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /user/installations_ 
  *resource*: appslist_installations_for_authenticated_user  
  *description*: Lists installations of your GitHub App that the authenticated user has explicit permission (`:read`, `:write`, or `:admin`) to access.  The authenticated user has explicit permission to access repositories they own, repositories where they are a collaborator, and repositories that they can access through an organization membership.  You can find the permissions for the installation under the `permissions` key.
* _GET /users/{username}/installation_ 
  *resource*: appsget_user_installation  
  *description*: Enables an authenticated GitHub App to find the user’s installation information.  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /apps/{app_slug}_ 
  *resource*: appsget_by_slug  
  *description*: > [!NOTE] > The `:app_slug` is just the URL-friendly name of your GitHub App. You can find this on the settings page for your GitHub App (e.g., `https://github.com/settings/apps/:app_slug`).
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/apps_ 
  *resource*: reposget_apps_with_access_to_protected_branch  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.  Lists the GitHub Apps that have push access to this branch. Only GitHub Apps that are installed on the repository and that have been granted write access to the repository contents can be added as authorized actors on a protected branch.
* _GET /app/installation-requests_ 
  *resource*: appslist_installation_requests_for_authenticated_app  
  *description*: Lists all the pending installation requests for the authenticated GitHub App.
* _GET /orgs/{org}/interaction-limits_ 
  *resource*: interactionsget_restrictions_for_org  
  *description*: Shows which type of GitHub user can interact with this organization and when the restriction expires. If there is no restrictions, you will see an empty response.
* _GET /repos/{owner}/{repo}/interaction-limits_ 
  *resource*: interactionsget_restrictions_for_repo  
  *description*: Shows which type of GitHub user can interact with this repository and when the restriction expires. If there are no restrictions, you will see an empty response.
* _GET /user/interaction-limits_ 
  *resource*: interactionsget_restrictions_for_authenticated_user  
  *description*: Shows which type of GitHub user can interact with your public repositories and when the restriction expires.
* _GET /issues_ 
  *resource*: issueslist  
  *description*: List issues assigned to the authenticated user across all visible repositories including owned repositories, member repositories, and organization repositories. You can use the `filter` query parameter to fetch issues that are not necessarily assigned to you.  > [!NOTE] > GitHub's REST API considers every pull request an issue, but not every issue is a pull request. For this reason, "Issues" endpoints may return both issues and pull requests in the response. You can identify pull requests by the `pull_request` key. Be aware that the `id` of a pull request returned from "Issues" endpoints will be an _issue id_. To find out the pull request id, use the "[List pull requests](https://docs.github.com/rest/pulls/pulls#list-pull-requests)" endpoint.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /orgs/{org}/issues_ 
  *resource*: issueslist_for_org  
  *description*: List issues in an organization assigned to the authenticated user.  > [!NOTE] > GitHub's REST API considers every pull request an issue, but not every issue is a pull request. For this reason, "Issues" endpoints may return both issues and pull requests in the response. You can identify pull requests by the `pull_request` key. Be aware that the `id` of a pull request returned from "Issues" endpoints will be an _issue id_. To find out the pull request id, use the "[List pull requests](https://docs.github.com/rest/pulls/pulls#list-pull-requests)" endpoint.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/issues_ 
  *resource*: issueslist_for_repo  
  *description*: List issues in a repository. Only open issues will be listed.  > [!NOTE] > GitHub's REST API considers every pull request an issue, but not every issue is a pull request. For this reason, "Issues" endpoints may return both issues and pull requests in the response. You can identify pull requests by the `pull_request` key. Be aware that the `id` of a pull request returned from "Issues" endpoints will be an _issue id_. To find out the pull request id, use the "[List pull requests](https://docs.github.com/rest/pulls/pulls#list-pull-requests)" endpoint.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/issues/{issue_number}_ 
  *resource*: issuesget  
  *description*: The API returns a [`301 Moved Permanently` status](https://docs.github.com/rest/guides/best-practices-for-using-the-rest-api#follow-redirects) if the issue was [transferred](https://docs.github.com/articles/transferring-an-issue-to-another-repository/) to another repository. If the issue was transferred to or deleted from a repository where the authenticated user lacks read access, the API returns a `404 Not Found` status. If the issue was deleted from a repository where the authenticated user has read access, the API returns a `410 Gone` status. To receive webhook events for transferred and deleted issues, subscribe to the [`issues`](https://docs.github.com/webhooks/event-payloads/#issues) webhook.  > [!NOTE] > GitHub's REST API considers every pull request an issue, but not every issue is a pull request. For this reason, "Issues" endpoints may return both issues and pull requests in the response. You can identify pull requests by the `pull_request` key. Be aware that the `id` of a pull request returned from "Issues" endpoints will be an _issue id_. To find out the pull request id, use the "[List pull requests](https://docs.github.com/rest/pulls/pulls#list-pull-requests)" endpoint.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /user/issues_ 
  *resource*: issueslist_for_authenticated_user  
  *description*: List issues across owned and member repositories assigned to the authenticated user.  > [!NOTE] > GitHub's REST API considers every pull request an issue, but not every issue is a pull request. For this reason, "Issues" endpoints may return both issues and pull requests in the response. You can identify pull requests by the `pull_request` key. Be aware that the `id` of a pull request returned from "Issues" endpoints will be an _issue id_. To find out the pull request id, use the "[List pull requests](https://docs.github.com/rest/pulls/pulls#list-pull-requests)" endpoint.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/issues/comments_ 
  *resource*: issueslist_comments_for_repo  
  *description*: You can use the REST API to list comments on issues and pull requests for a repository. Every pull request is an issue, but not every issue is a pull request.  By default, issue comments are ordered by ascending ID.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/issues/comments/{comment_id}_ 
  *resource*: issuesget_comment  
  *description*: You can use the REST API to get comments on issues and pull requests. Every pull request is an issue, but not every issue is a pull request.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/issues/{issue_number}/comments_ 
  *resource*: issueslist_comments  
  *description*: You can use the REST API to list comments on issues and pull requests. Every pull request is an issue, but not every issue is a pull request.  Issue comments are ordered by ascending ID.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/issues/events_ 
  *resource*: issueslist_events_for_repo  
  *description*: Lists events for a repository.
* _GET /repos/{owner}/{repo}/issues/events/{event_id}_ 
  *resource*: issuesget_event  
  *description*: Gets a single event by the event id.
* _GET /repos/{owner}/{repo}/issues/{issue_number}/events_ 
  *resource*: issueslist_events  
  *description*: Lists all events for an issue.
* _GET /search/issues_ 
  *resource*: searchissues_and_pull_requests  
  *description*: Find issues by state and keyword. This method returns up to 100 results [per page](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api).  When searching for issues, you can get text match metadata for the issue **title**, issue **body**, and issue **comment body** fields when you pass the `text-match` media type. For more details about how to receive highlighted search results, see [Text match metadata](https://docs.github.com/rest/search/search#text-match-metadata).  For example, if you want to find the oldest unresolved Python bugs on Windows. Your query might look something like this.  `q=windows+label:bug+language:python+state:open&sort=created&order=asc`  This query searches for the keyword `windows`, within any open issue that is labeled as `bug`. The search runs across repositories whose primary language is Python. The results are sorted by creation date in ascending order, which means the oldest issues appear first in the search results.  > [!NOTE] > For requests made by GitHub Apps with a user access token, you can't retrieve a combination of issues and pull requests in a single query. Requests that don't include the `is:issue` or `is:pull-request` qualifier will receive an HTTP `422 Unprocessable Entity` response. To get results for both issues and pull requests, you must send separate queries for issues and pull requests. For more information about the `is` qualifier, see "[Searching only issues or pull requests](https://docs.github.com/github/searching-for-information-on-github/searching-issues-and-pull-requests#search-only-issues-or-pull-requests)."
* _GET /repos/{owner}/{repo}/actions/jobs/{job_id}_ 
  *resource*: actionsget_job_for_workflow_run  
  *description*: Gets a specific job in a workflow run.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/jobs_ 
  *resource*: actionslist_jobs_for_workflow_run_attempt  
  *description*: Lists jobs for a specific workflow run attempt. You can use parameters to narrow the list of results. For more information about using parameters, see [Parameters](https://docs.github.com/rest/guides/getting-started-with-the-rest-api#parameters).  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint  with a private repository.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs_ 
  *resource*: actionslist_jobs_for_workflow_run  
  *description*: Lists jobs for a workflow run. You can use parameters to narrow the list of results. For more information about using parameters, see [Parameters](https://docs.github.com/rest/guides/getting-started-with-the-rest-api#parameters).  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /user/keys_ 
  *resource*: userslist_public_ssh_keys_for_authenticated_user  
  *description*: Lists the public SSH keys for the authenticated user's GitHub account.  OAuth app tokens and personal access tokens (classic) need the `read:public_key` scope to use this endpoint.
* _GET /user/keys/{key_id}_ 
  *resource*: usersget_public_ssh_key_for_authenticated_user  
  *description*: View extended details for a single public SSH key.  OAuth app tokens and personal access tokens (classic) need the `read:public_key` scope to use this endpoint.
* _GET /users/{username}/keys_ 
  *resource*: userslist_public_keys_for_user  
  *description*: Lists the _verified_ public SSH keys for a user. This is accessible by anyone.
* _GET /repos/{owner}/{repo}/issues/{issue_number}/labels_ 
  *resource*: issueslist_labels_on_issue  
  *description*: Lists all labels for an issue.
* _GET /repos/{owner}/{repo}/labels_ 
  *resource*: issueslist_labels_for_repo  
  *description*: Lists all labels for a repository.
* _GET /repos/{owner}/{repo}/labels/{name}_ 
  *resource*: issuesget_label  
  *description*: Gets a label using the given name.
* _GET /repos/{owner}/{repo}/milestones/{milestone_number}/labels_ 
  *resource*: issueslist_labels_for_milestone  
  *description*: Lists labels for issues in a milestone.
* _GET /search/labels_ 
  *resource*: searchlabels  
  *description*: Find labels in a repository with names or descriptions that match search keywords. Returns up to 100 results [per page](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api).  When searching for labels, you can get text match metadata for the label **name** and **description** fields when you pass the `text-match` media type. For more details about how to receive highlighted search results, see [Text match metadata](https://docs.github.com/rest/search/search#text-match-metadata).  For example, if you want to find labels in the `linguist` repository that match `bug`, `defect`, or `enhancement`. Your query might look like this:  `q=bug+defect+enhancement&repository_id=64778136`  The labels that best match the query appear first in the search results.
* _GET /repos/{owner}/{repo}/languages_ 
  *resource*: reposlist_languages  
  *description*: Lists languages for the specified repository. The value shown for each language is the number of bytes of code written in that language.
* _GET /licenses/{license}_ 
  *resource*: licensesget  
  *description*: Gets information about a specific license. For more information, see "[Licensing a repository ](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)."
* _GET /repos/{owner}/{repo}/license_ 
  *resource*: licensesget_for_repo  
  *description*: This method returns the contents of the repository's license file, if one is detected.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw contents of the license. - **`application/vnd.github.html+json`**: Returns the license contents in HTML. Markup languages are rendered to HTML using GitHub's open-source [Markup library](https://github.com/github/markup).
* _GET /licenses_ 
  *resource*: licensesget_all_commonly_used  
  *description*: Lists the most commonly used licenses on GitHub. For more information, see "[Licensing a repository ](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)."
* _GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs_ 
  *resource*: actionsdownload_job_logs_for_workflow_run  
  *description*: Gets a redirect URL to download a plain text file of logs for a workflow job. This link expires after 1 minute. Look for `Location:` in the response header to find the URL for the download.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}/logs_ 
  *resource*: actionsdownload_workflow_run_attempt_logs  
  *description*: Gets a redirect URL to download an archive of log files for a specific workflow run attempt. This link expires after 1 minute. Look for `Location:` in the response header to find the URL for the download.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/logs_ 
  *resource*: actionsdownload_workflow_run_logs  
  *description*: Gets a redirect URL to download an archive of log files for a workflow run. This link expires after 1 minute. Look for `Location:` in the response header to find the URL for the download.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /marketplace_listing/plans_ 
  *resource*: appslist_plans  
  *description*: Lists all plans that are part of your GitHub Marketplace listing.  GitHub Apps must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint. OAuth apps must use [basic authentication](https://docs.github.com/rest/authentication/authenticating-to-the-rest-api#using-basic-authentication) with their client ID and client secret to access this endpoint.
* _GET /marketplace_listing/stubbed/plans_ 
  *resource*: appslist_plans_stubbed  
  *description*: Lists all plans that are part of your GitHub Marketplace listing.  GitHub Apps must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint. OAuth apps must use [basic authentication](https://docs.github.com/rest/authentication/authenticating-to-the-rest-api#using-basic-authentication) with their client ID and client secret to access this endpoint.
* _GET /marketplace_listing/accounts/{account_id}_ 
  *resource*: appsget_subscription_plan_for_account  
  *description*: Shows whether the user or organization account actively subscribes to a plan listed by the authenticated GitHub App. When someone submits a plan change that won't be processed until the end of their billing cycle, you will also see the upcoming pending change.  GitHub Apps must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint. OAuth apps must use [basic authentication](https://docs.github.com/rest/authentication/authenticating-to-the-rest-api#using-basic-authentication) with their client ID and client secret to access this endpoint.
* _GET /marketplace_listing/plans/{plan_id}/accounts_ 
  *resource*: appslist_accounts_for_plan  
  *description*: Returns user and organization accounts associated with the specified plan, including free plans. For per-seat pricing, you see the list of accounts that have purchased the plan, including the number of seats purchased. When someone submits a plan change that won't be processed until the end of their billing cycle, you will also see the upcoming pending change.  GitHub Apps must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint. OAuth apps must use [basic authentication](https://docs.github.com/rest/authentication/authenticating-to-the-rest-api#using-basic-authentication) with their client ID and client secret to access this endpoint.
* _GET /marketplace_listing/stubbed/accounts/{account_id}_ 
  *resource*: appsget_subscription_plan_for_account_stubbed  
  *description*: Shows whether the user or organization account actively subscribes to a plan listed by the authenticated GitHub App. When someone submits a plan change that won't be processed until the end of their billing cycle, you will also see the upcoming pending change.  GitHub Apps must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint. OAuth apps must use [basic authentication](https://docs.github.com/rest/authentication/authenticating-to-the-rest-api#using-basic-authentication) with their client ID and client secret to access this endpoint.
* _GET /marketplace_listing/stubbed/plans/{plan_id}/accounts_ 
  *resource*: appslist_accounts_for_plan_stubbed  
  *description*: Returns repository and organization accounts associated with the specified plan, including free plans. For per-seat pricing, you see the list of accounts that have purchased the plan, including the number of seats purchased. When someone submits a plan change that won't be processed until the end of their billing cycle, you will also see the upcoming pending change.  GitHub Apps must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint. OAuth apps must use [basic authentication](https://docs.github.com/rest/authentication/authenticating-to-the-rest-api#using-basic-authentication) with their client ID and client secret to access this endpoint.
* _GET /orgs/{org}/members/{username}_ 
  *resource*: orgscheck_membership_for_user  
  *description*: Check if a user is, publicly or privately, a member of the organization.
* _GET /teams/{team_id}/members/{username}_ 
  *resource*: teamsget_member_legacy  
  *description*: The "Get team member" endpoint (described below) is deprecated.  We recommend using the [Get team membership for a user](https://docs.github.com/rest/teams/members#get-team-membership-for-a-user) endpoint instead. It allows you to get both active and pending memberships.  To list members in a team, the team must be visible to the authenticated user.
* _GET /repos/{owner}/{repo}/pulls/{pull_number}/merge_ 
  *resource*: pullscheck_if_merged  
  *description*: Checks if a pull request has been merged into the base branch. The HTTP status of the response indicates whether or not the pull request has been merged; the response body is empty.
* _GET /meta_ 
  *resource*: metaget  
  *description*: Returns meta information about GitHub, including a list of GitHub's IP addresses. For more information, see "[About GitHub's IP addresses](https://docs.github.com/articles/about-github-s-ip-addresses/)."  The API's response also includes a list of GitHub's domain names.  The values shown in the documentation's response are example values. You must always query the API directly to get the latest values.  > [!NOTE] > This endpoint returns both IPv4 and IPv6 addresses. However, not all features support IPv6. You should refer to the specific documentation for each feature to determine if IPv6 is supported.
* _GET /orgs/{org}/migrations_ 
  *resource*: migrationslist_for_org  
  *description*: Lists the most recent migrations, including both exports (which can be started through the REST API) and imports (which cannot be started using the REST API).  A list of `repositories` is only returned for export migrations.
* _GET /orgs/{org}/migrations/{migration_id}_ 
  *resource*: migrationsget_status_for_org  
  *description*: Fetches the status of a migration.  The `state` of a migration can be one of the following values:  *   `pending`, which means the migration hasn't started yet. *   `exporting`, which means the migration is in progress. *   `exported`, which means the migration finished successfully. *   `failed`, which means the migration failed.
* _GET /user/migrations_ 
  *resource*: migrationslist_for_authenticated_user  
  *description*: Lists all migrations a user has started.
* _GET /user/migrations/{migration_id}_ 
  *resource*: migrationsget_status_for_authenticated_user  
  *description*: Fetches a single user migration. The response includes the `state` of the migration, which can be one of the following values:  *   `pending` - the migration hasn't started yet. *   `exporting` - the migration is in progress. *   `exported` - the migration finished successfully. *   `failed` - the migration failed.  Once the migration has been `exported` you can [download the migration archive](https://docs.github.com/rest/migrations/users#download-a-user-migration-archive).
* _GET /repos/{owner}/{repo}/milestones_ 
  *resource*: issueslist_milestones  
  *description*: Lists milestones for a repository.
* _GET /repos/{owner}/{repo}/milestones/{milestone_number}_ 
  *resource*: issuesget_milestone  
  *description*: Gets a milestone using the given milestone number.
* _GET /orgs/{org}/actions/secrets/{secret_name}/repositories_ 
  *resource*: actionslist_selected_repos_for_org_secret  
  *description*: Lists all repositories that have been selected when the `visibility` for repository access to a secret is set to `selected`.  Authenticated users must have collaborator access to a repository to create, update, or read secrets.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint. If the repository is private, the `repo` scope is also required.
* _GET /orgs/{org}/actions/variables/{name}/repositories_ 
  *resource*: actionslist_selected_repos_for_org_variable  
  *description*: Lists all repositories that can access an organization variable that is available to selected repositories.  Authenticated users must have collaborator access to a repository to create, update, or read variables.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint. If the repository is private, the `repo` scope is also required.
* _GET /orgs/{org}/codespaces/secrets/{secret_name}/repositories_ 
  *resource*: codespaceslist_selected_repos_for_org_secret  
  *description*: Lists all repositories that have been selected when the `visibility` for repository access to a secret is set to `selected`.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}/dependabot/secrets/{secret_name}/repositories_ 
  *resource*: dependabotlist_selected_repos_for_org_secret  
  *description*: Lists all repositories that have been selected when the `visibility` for repository access to a secret is set to `selected`.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}/migrations/{migration_id}/repositories_ 
  *resource*: migrationslist_repos_for_org  
  *description*: List all the repositories for this organization migration.
* _GET /orgs/{org}/personal-access-token-requests/{pat_request_id}/repositories_ 
  *resource*: orgslist_pat_grant_request_repositories  
  *description*: Lists the repositories a fine-grained personal access token request is requesting access to.  Only GitHub Apps can use this endpoint.
* _GET /orgs/{org}/personal-access-tokens/{pat_id}/repositories_ 
  *resource*: orgslist_pat_grant_repositories  
  *description*: Lists the repositories a fine-grained personal access token has access to.  Only GitHub Apps can use this endpoint.
* _GET /orgs/{org}/repos_ 
  *resource*: reposlist_for_org  
  *description*: Lists repositories for the specified organization.  > [!NOTE] > In order to see the `security_and_analysis` block for a repository you must have admin permissions for the repository or be an owner or security manager for the organization that owns the repository. For more information, see "[Managing security managers in your organization](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization)."
* _GET /orgs/{org}/teams/{team_slug}/repos_ 
  *resource*: teamslist_repos_in_org  
  *description*: Lists a team's repositories visible to the authenticated user.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/repos`.
* _GET /repos/{owner}/{repo}/forks_ 
  *resource*: reposlist_forks  
* _GET /repositories_ 
  *resource*: reposlist_public  
  *description*: Lists all public repositories in the order that they were created.  Note: - For GitHub Enterprise Server, this endpoint will only list repositories available to all users on the enterprise. - Pagination is powered exclusively by the `since` parameter. Use the [Link header](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api#using-link-headers) to get the URL for the next page of repositories.
* _GET /teams/{team_id}/repos_ 
  *resource*: teamslist_repos_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [List team repositories](https://docs.github.com/rest/teams/teams#list-team-repositories) endpoint.
* _GET /user/codespaces/secrets/{secret_name}/repositories_ 
  *resource*: codespaceslist_repositories_for_secret_for_authenticated_user  
  *description*: List the repositories that have been granted the ability to use a user's development environment secret.  The authenticated user must have Codespaces access to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `codespace` or `codespace:secrets` scope to use this endpoint.
* _GET /user/migrations/{migration_id}/repositories_ 
  *resource*: migrationslist_repos_for_authenticated_user  
  *description*: Lists all the repositories for this user migration.
* _GET /user/subscriptions_ 
  *resource*: activitylist_watched_repos_for_authenticated_user  
  *description*: Lists repositories the authenticated user is watching.
* _GET /users/{username}/repos_ 
  *resource*: reposlist_for_user  
  *description*: Lists public repositories for the specified user.
* _GET /users/{username}/subscriptions_ 
  *resource*: activitylist_repos_watched_by_user  
  *description*: Lists repositories a user is watching.
* _GET /repos/{owner}/{repo}/codespaces/new_ 
  *resource*: codespacespre_flight_with_repo_for_authenticated_user  
  *description*: Gets the default attributes for codespaces created by the user with the repository.  OAuth app tokens and personal access tokens (classic) need the `codespace` scope to use this endpoint.
* _GET /octocat_ 
  *resource*: metaget_octocat  
  *description*: Get the octocat as ASCII art
* _GET /orgs/{org}/properties/schema_ 
  *resource*: orgsget_all_custom_properties  
  *description*: Gets all custom properties defined for an organization. Organization members can read these properties.
* _GET /orgs/{org}/properties/schema/{custom_property_name}_ 
  *resource*: orgsget_custom_property  
  *description*: Gets a custom property that is defined for an organization. Organization members can read these properties.
* _GET /orgs/{org}/hooks_ 
  *resource*: orgslist_webhooks  
  *description*: You must be an organization owner to use this endpoint.  OAuth app tokens and personal access tokens (classic) need `admin:org_hook` scope. OAuth apps cannot list, view, or edit webhooks that they did not create and users cannot list, view, or edit webhooks that were created by OAuth apps.
* _GET /orgs/{org}/hooks/{hook_id}_ 
  *resource*: orgsget_webhook  
  *description*: Returns a webhook configured in an organization. To get only the webhook `config` properties, see "[Get a webhook configuration for an organization](/rest/orgs/webhooks#get-a-webhook-configuration-for-an-organization).  You must be an organization owner to use this endpoint.  OAuth app tokens and personal access tokens (classic) need `admin:org_hook` scope. OAuth apps cannot list, view, or edit webhooks that they did not create and users cannot list, view, or edit webhooks that were created by OAuth apps.
* _GET /orgs/{org}/memberships/{username}_ 
  *resource*: orgsget_membership_for_user  
  *description*: In order to get a user's membership with an organization, the authenticated user must be an organization member. The `state` parameter in the response can be used to identify the user's membership status.
* _GET /user/memberships/orgs_ 
  *resource*: orgslist_memberships_for_authenticated_user  
  *description*: Lists all of the authenticated user's organization memberships.
* _GET /user/memberships/orgs/{org}_ 
  *resource*: orgsget_membership_for_authenticated_user  
  *description*: If the authenticated user is an active or pending member of the organization, this endpoint will return the user's membership. If the authenticated user is not affiliated with the organization, a `404` is returned. This endpoint will return a `403` if the request is made by a GitHub App that is blocked by the organization.
* _GET /orgs/{org}/properties/values_ 
  *resource*: orgslist_custom_properties_values_for_repos  
  *description*: Lists organization repositories with all of their custom property values. Organization members can read these properties.
* _GET /orgs/{org}/actions/secrets_ 
  *resource*: actionslist_org_secrets  
  *description*: Lists all secrets available in an organization without revealing their encrypted values.  Authenticated users must have collaborator access to a repository to create, update, or read secrets.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint. If the repository is private, the `repo` scope is also required.
* _GET /orgs/{org}/actions/secrets/{secret_name}_ 
  *resource*: actionsget_org_secret  
  *description*: Gets a single organization secret without revealing its encrypted value.  The authenticated user must have collaborator access to a repository to create, update, or read secrets  OAuth tokens and personal access tokens (classic) need the`admin:org` scope to use this endpoint. If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /orgs/{org}/actions/variables_ 
  *resource*: actionslist_org_variables  
  *description*: Lists all organization variables.  Authenticated users must have collaborator access to a repository to create, update, or read variables.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint. If the repository is private, the `repo` scope is also required.
* _GET /orgs/{org}/actions/variables/{name}_ 
  *resource*: actionsget_org_variable  
  *description*: Gets a specific variable in an organization.  The authenticated user must have collaborator access to a repository to create, update, or read variables.  OAuth tokens and personal access tokens (classic) need the`admin:org` scope to use this endpoint. If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /orgs/{org}/dependabot/secrets_ 
  *resource*: dependabotlist_org_secrets  
  *description*: Lists all secrets available in an organization without revealing their encrypted values.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}/dependabot/secrets/{secret_name}_ 
  *resource*: dependabotget_org_secret  
  *description*: Gets a single organization secret without revealing its encrypted value.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}_ 
  *resource*: orgsget  
  *description*: Gets information about an organization.  When the value of `two_factor_requirement_enabled` is `true`, the organization requires all members, billing managers, and outside collaborators to enable [two-factor authentication](https://docs.github.com/articles/securing-your-account-with-two-factor-authentication-2fa/).  To see the full details about an organization, the authenticated user must be an organization owner.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to see the full details about an organization.  To see information about an organization's GitHub plan, GitHub Apps need the `Organization plan` permission.
* _GET /orgs/{org}/failed_invitations_ 
  *resource*: orgslist_failed_invitations  
  *description*: The return hash contains `failed_at` and `failed_reason` fields which represent the time at which the invitation failed and the reason for the failure.
* _GET /orgs/{org}/invitations_ 
  *resource*: orgslist_pending_invitations  
  *description*: The return hash contains a `role` field which refers to the Organization Invitation role and will be one of the following values: `direct_member`, `admin`, `billing_manager`, or `hiring_manager`. If the invitee is not a GitHub member, the `login` field in the return hash will be `null`.
* _GET /orgs/{org}/teams/{team_slug}/invitations_ 
  *resource*: teamslist_pending_invitations_in_org  
  *description*: The return hash contains a `role` field which refers to the Organization Invitation role and will be one of the following values: `direct_member`, `admin`, `billing_manager`, `hiring_manager`, or `reinstate`. If the invitee is not a GitHub member, the `login` field in the return hash will be `null`.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/invitations`.
* _GET /teams/{team_id}/invitations_ 
  *resource*: teamslist_pending_invitations_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [`List pending team invitations`](https://docs.github.com/rest/teams/members#list-pending-team-invitations) endpoint.  The return hash contains a `role` field which refers to the Organization Invitation role and will be one of the following values: `direct_member`, `admin`, `billing_manager`, `hiring_manager`, or `reinstate`. If the invitee is not a GitHub member, the `login` field in the return hash will be `null`.
* _GET /orgs/{org}/personal-access-tokens_ 
  *resource*: orgslist_pat_grants  
  *description*: Lists approved fine-grained personal access tokens owned by organization members that can access organization resources.  Only GitHub Apps can use this endpoint.
* _GET /orgs/{org}/personal-access-token-requests_ 
  *resource*: orgslist_pat_grant_requests  
  *description*: Lists requests from organization members to access organization resources with a fine-grained personal access token.  Only GitHub Apps can use this endpoint.
* _GET /orgs/{org}/organization-roles_ 
  *resource*: orgslist_org_roles  
  *description*: Lists the organization roles available in this organization. For more information on organization roles, see "[Using organization roles](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/using-organization-roles)."  To use this endpoint, the authenticated user must be one of:  - An administrator for the organization. - A user, or a user on a team, with the fine-grained permissions of `read_organization_custom_org_role` in the organization.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}/organization-roles/{role_id}_ 
  *resource*: orgsget_org_role  
  *description*: Gets an organization role that is available to this organization. For more information on organization roles, see "[Using organization roles](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/using-organization-roles)."  To use this endpoint, the authenticated user must be one of:  - An administrator for the organization. - A user, or a user on a team, with the fine-grained permissions of `read_organization_custom_org_role` in the organization.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /enterprises/{enterprise}/secret-scanning/alerts_ 
  *resource*: secret_scanninglist_alerts_for_enterprise  
  *description*: Lists secret scanning alerts for eligible repositories in an enterprise, from newest to oldest.  Alerts are only returned for organizations in the enterprise for which the authenticated user is an organization owner or a [security manager](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization).  The authenticated user must be a member of the enterprise in order to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope or `security_events` scope to use this endpoint.
* _GET /orgs/{org}/secret-scanning/alerts_ 
  *resource*: secret_scanninglist_alerts_for_org  
  *description*: Lists secret scanning alerts for eligible repositories in an organization, from newest to oldest.  The authenticated user must be an administrator or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` or `security_events` scope to use this endpoint. If this endpoint is only used with public repositories, the token can use the `public_repo` scope instead.
* _GET /organizations_ 
  *resource*: orgslist  
  *description*: Lists all organizations, in the order that they were created.  > [!NOTE] > Pagination is powered exclusively by the `since` parameter. Use the [Link header](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api#using-link-headers) to get the URL for the next page of organizations.
* _GET /user/orgs_ 
  *resource*: orgslist_for_authenticated_user  
  *description*: List organizations for the authenticated user.  For OAuth app tokens and personal access tokens (classic), this endpoint only lists organizations that your authorization allows you to operate on in some way (e.g., you can list teams with `read:org` scope, you can publicize your organization membership with `user` scope, etc.). Therefore, this API requires at least `user` or `read:org` scope for OAuth app tokens and personal access tokens (classic). Requests with insufficient scope will receive a `403 Forbidden` response.
* _GET /users/{username}/orgs_ 
  *resource*: orgslist_for_user  
  *description*: List [public organization memberships](https://docs.github.com/articles/publicizing-or-concealing-organization-membership) for the specified user.  This method only lists _public_ memberships, regardless of authentication. If you need to fetch all of the organization memberships (public and private) for the authenticated user, use the [List organizations for the authenticated user](https://docs.github.com/rest/orgs/orgs#list-organizations-for-the-authenticated-user) API instead.
* _GET /orgs/{org}/docker/conflicts_ 
  *resource*: packageslist_docker_migration_conflicting_packages_for_organization  
  *description*: Lists all packages that are in a specific organization, are readable by the requesting user, and that encountered a conflict during a Docker migration.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint.
* _GET /orgs/{org}/packages_ 
  *resource*: packageslist_packages_for_organization  
  *description*: Lists packages in an organization readable by the user.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /orgs/{org}/packages/{package_type}/{package_name}_ 
  *resource*: packagesget_package_for_organization  
  *description*: Gets a specific package in an organization.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /user/docker/conflicts_ 
  *resource*: packageslist_docker_migration_conflicting_packages_for_authenticated_user  
  *description*: Lists all packages that are owned by the authenticated user within the user's namespace, and that encountered a conflict during a Docker migration.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint.
* _GET /user/packages_ 
  *resource*: packageslist_packages_for_authenticated_user  
  *description*: Lists packages owned by the authenticated user within the user's namespace.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /user/packages/{package_type}/{package_name}_ 
  *resource*: packagesget_package_for_authenticated_user  
  *description*: Gets a specific package for a package owned by the authenticated user.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /users/{username}/docker/conflicts_ 
  *resource*: packageslist_docker_migration_conflicting_packages_for_user  
  *description*: Lists all packages that are in a specific user's namespace, that the requesting user has access to, and that encountered a conflict during Docker migration.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint.
* _GET /users/{username}/packages_ 
  *resource*: packageslist_packages_for_user  
  *description*: Lists all packages in a user's namespace for which the requesting user has access.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /users/{username}/packages/{package_type}/{package_name}_ 
  *resource*: packagesget_package_for_user  
  *description*: Gets a specific package metadata for a public package owned by a user.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /orgs/{org}/packages/{package_type}/{package_name}/versions_ 
  *resource*: packagesget_all_package_versions_for_package_owned_by_org  
  *description*: Lists package versions for a package owned by an organization.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint if the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /orgs/{org}/packages/{package_type}/{package_name}/versions/{package_version_id}_ 
  *resource*: packagesget_package_version_for_organization  
  *description*: Gets a specific package version in an organization.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /user/packages/{package_type}/{package_name}/versions_ 
  *resource*: packagesget_all_package_versions_for_package_owned_by_authenticated_user  
  *description*: Lists package versions for a package owned by the authenticated user.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /user/packages/{package_type}/{package_name}/versions/{package_version_id}_ 
  *resource*: packagesget_package_version_for_authenticated_user  
  *description*: Gets a specific package version for a package owned by the authenticated user.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /users/{username}/packages/{package_type}/{package_name}/versions_ 
  *resource*: packagesget_all_package_versions_for_package_owned_by_user  
  *description*: Lists package versions for a public package owned by a specified user.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /users/{username}/packages/{package_type}/{package_name}/versions/{package_version_id}_ 
  *resource*: packagesget_package_version_for_user  
  *description*: Gets a specific package version for a public package owned by a specified user.  OAuth app tokens and personal access tokens (classic) need the `read:packages` scope to use this endpoint. If the `package_type` belongs to a GitHub Packages registry that only supports repository-scoped permissions, the `repo` scope is also required. For the list of these registries, see "[About permissions for GitHub Packages](https://docs.github.com/packages/learn-github-packages/about-permissions-for-github-packages#permissions-for-repository-scoped-packages)."
* _GET /orgs/{org}/settings/billing/packages_ 
  *resource*: billingget_github_packages_billing_org  
  *description*: Gets the free and paid storage used for GitHub Packages in gigabytes.  Paid minutes only apply to packages stored for private repositories. For more information, see "[Managing billing for GitHub Packages](https://docs.github.com/github/setting-up-and-managing-billing-and-payments-on-github/managing-billing-for-github-packages)."  OAuth app tokens and personal access tokens (classic) need the `repo` or `admin:org` scope to use this endpoint.
* _GET /users/{username}/settings/billing/packages_ 
  *resource*: billingget_github_packages_billing_user  
  *description*: Gets the free and paid storage used for GitHub Packages in gigabytes.  Paid minutes only apply to packages stored for private repositories. For more information, see "[Managing billing for GitHub Packages](https://docs.github.com/github/setting-up-and-managing-billing-and-payments-on-github/managing-billing-for-github-packages)."  OAuth app tokens and personal access tokens (classic) need the `user` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/pages_ 
  *resource*: reposget_pages  
  *description*: Gets information about a GitHub Pages site.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/pages/builds_ 
  *resource*: reposlist_pages_builds  
  *description*: Lists builts of a GitHub Pages site.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/pages/builds/latest_ 
  *resource*: reposget_latest_pages_build  
  *description*: Gets information about the single most recent build of a GitHub Pages site.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/pages/builds/{build_id}_ 
  *resource*: reposget_pages_build  
  *description*: Gets information about a GitHub Pages build.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/pages/deployments/{pages_deployment_id}_ 
  *resource*: reposget_pages_deployment  
  *description*: Gets the current status of a GitHub Pages deployment.  The authenticated user must have read permission for the GitHub Pages site.
* _GET /repos/{owner}/{repo}/pages/health_ 
  *resource*: reposget_pages_health_check  
  *description*: Gets a health check of the DNS settings for the `CNAME` record configured for a repository's GitHub Pages.  The first request to this endpoint returns a `202 Accepted` status and starts an asynchronous background task to get the results for the domain. After the background task completes, subsequent requests to this endpoint return a `200 OK` status with the health check results in the response.  The authenticated user must be a repository administrator, maintainer, or have the 'manage GitHub Pages settings' permission to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/stats/participation_ 
  *resource*: reposget_participation_stats  
  *description*: Returns the total commit counts for the `owner` and total commit counts in `all`. `all` is everyone combined, including the `owner` in the last 52 weeks. If you'd like to get the commit counts for non-owners, you can subtract `owner` from `all`.  The array order is oldest week (index 0) to most recent week.  The most recent week is seven days ago at UTC midnight to today at UTC midnight.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/pending_deployments_ 
  *resource*: actionsget_pending_deployments_for_run  
  *description*: Get all deployment environments for a workflow run that are waiting for protection rules to pass.  Anyone with read access to the repository can use this endpoint.  If the repository is private, OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/import/authors_ 
  *resource*: migrationsget_commit_authors  
  *description*: Each type of source control system represents authors in a different way. For example, a Git commit author has a display name and an email address, but a Subversion commit author just has a username. The GitHub Importer will make the author information valid, but the author might not be correct. For example, it will change the bare Subversion username `hubot` into something like `hubot <hubot@12341234-abab-fefe-8787-fedcba987654>`.  This endpoint and the [Map a commit author](https://docs.github.com/rest/migrations/source-imports#map-a-commit-author) endpoint allow you to provide correct Git author information.  > [!WARNING] > **Deprecation notice:** Due to very low levels of usage and available alternatives, this endpoint is deprecated and will no longer be available from 00:00 UTC on April 12, 2024. For more details and alternatives, see the [changelog](https://gh.io/source-imports-api-deprecation).
* _GET /repos/{owner}/{repo}/import/large_files_ 
  *resource*: migrationsget_large_files  
  *description*: List files larger than 100MB found during the import  > [!WARNING] > **Deprecation notice:** Due to very low levels of usage and available alternatives, this endpoint is deprecated and will no longer be available from 00:00 UTC on April 12, 2024. For more details and alternatives, see the [changelog](https://gh.io/source-imports-api-deprecation).
* _GET /repos/{owner}/{repo}/private-vulnerability-reporting_ 
  *resource*: reposcheck_private_vulnerability_reporting  
  *description*: Returns a boolean indicating whether or not private vulnerability reporting is enabled for the repository. For more information, see "[Evaluating the security settings of a repository](https://docs.github.com/code-security/security-advisories/working-with-repository-security-advisories/evaluating-the-security-settings-of-a-repository)".
* _GET /orgs/{org}/projects_ 
  *resource*: projectslist_for_org  
  *description*: Lists the projects in an organization. Returns a `404 Not Found` status if projects are disabled in the organization. If you do not have sufficient privileges to perform this action, a `401 Unauthorized` or `410 Gone` status is returned.
* _GET /projects/{project_id}_ 
  *resource*: projectsget  
  *description*: Gets a project by its `id`. Returns a `404 Not Found` status if projects are disabled. If you do not have sufficient privileges to perform this action, a `401 Unauthorized` or `410 Gone` status is returned.
* _GET /repos/{owner}/{repo}/projects_ 
  *resource*: projectslist_for_repo  
  *description*: Lists the projects in a repository. Returns a `404 Not Found` status if projects are disabled in the repository. If you do not have sufficient privileges to perform this action, a `401 Unauthorized` or `410 Gone` status is returned.
* _GET /users/{username}/projects_ 
  *resource*: projectslist_for_user  
  *description*: Lists projects for a user.
* _GET /projects/columns/cards/{card_id}_ 
  *resource*: projectsget_card  
  *description*: Gets information about a project card.
* _GET /projects/columns/{column_id}/cards_ 
  *resource*: projectslist_cards  
  *description*: Lists the project cards in a project.
* _GET /projects/{project_id}/collaborators/{username}/permission_ 
  *resource*: projectsget_permission_for_user  
  *description*: Returns the collaborator's permission level for an organization project. Possible values for the `permission` key: `admin`, `write`, `read`, `none`. You must be an organization owner or a project `admin` to review a user's permission level.
* _GET /projects/columns/{column_id}_ 
  *resource*: projectsget_column  
  *description*: Gets information about a project column.
* _GET /projects/{project_id}/columns_ 
  *resource*: projectslist_columns  
  *description*: Lists the project columns in a project.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/enforce_admins_ 
  *resource*: reposget_admin_branch_protection  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/required_signatures_ 
  *resource*: reposget_commit_signature_protection  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.  When authenticated with admin or owner permissions to the repository, you can use this endpoint to check whether a branch requires signed commits. An enabled status of `true` indicates you must sign commits on this branch. For more information, see [Signing commits with GPG](https://docs.github.com/articles/signing-commits-with-gpg) in GitHub Help.  > [!NOTE] > You must enable branch protection to require signed commits.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection_ 
  *resource*: reposget_branch_protection  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.
* _GET /orgs/{org}/public_members/{username}_ 
  *resource*: orgscheck_public_membership_for_user  
  *description*: Check if the provided user is a public member of the organization.
* _GET /repos/{owner}/{repo}/pulls/{pull_number}_ 
  *resource*: pullsget  
  *description*: Draft pull requests are available in public repositories with GitHub Free and GitHub Free for organizations, GitHub Pro, and legacy per-repository billing plans, and in public and private repositories with GitHub Team and GitHub Enterprise Cloud. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.  Lists details of a pull request by providing its number.  When you get, [create](https://docs.github.com/rest/pulls/pulls/#create-a-pull-request), or [edit](https://docs.github.com/rest/pulls/pulls#update-a-pull-request) a pull request, GitHub creates a merge commit to test whether the pull request can be automatically merged into the base branch. This test commit is not added to the base branch or the head branch. You can review the status of the test commit using the `mergeable` key. For more information, see "[Checking mergeability of pull requests](https://docs.github.com/rest/guides/getting-started-with-the-git-database-api#checking-mergeability-of-pull-requests)".  The value of the `mergeable` attribute can be `true`, `false`, or `null`. If the value is `null`, then GitHub has started a background job to compute the mergeability. After giving the job time to complete, resubmit the request. When the job finishes, you will see a non-`null` value for the `mergeable` attribute in the response. If `mergeable` is `true`, then `merge_commit_sha` will be the SHA of the _test_ merge commit.  The value of the `merge_commit_sha` attribute changes depending on the state of the pull request. Before merging a pull request, the `merge_commit_sha` attribute holds the SHA of the _test_ merge commit. After merging a pull request, the `merge_commit_sha` attribute changes depending on how you merged the pull request:  *   If merged as a [merge commit](https://docs.github.com/articles/about-merge-methods-on-github/), `merge_commit_sha` represents the SHA of the merge commit. *   If merged via a [squash](https://docs.github.com/articles/about-merge-methods-on-github/#squashing-your-merge-commits), `merge_commit_sha` represents the SHA of the squashed commit on the base branch. *   If [rebased](https://docs.github.com/articles/about-merge-methods-on-github/#rebasing-and-merging-your-commits), `merge_commit_sha` represents the commit that the base branch was updated to.  Pass the appropriate [media type](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types) to fetch diff and patch formats.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`. - **`application/vnd.github.diff`**: For more information, see "[git-diff](https://git-scm.com/docs/git-diff)" in the Git documentation. If a diff is corrupt, contact us through the [GitHub Support portal](https://support.github.com/). Include the repository name and pull request ID in your message.
* _GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews_ 
  *resource*: pullslist_reviews  
  *description*: Lists all reviews for a specified pull request. The list of reviews returns in chronological order.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}_ 
  *resource*: pullsget_review  
  *description*: Retrieves a pull request review by its ID.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/pulls/comments_ 
  *resource*: pullslist_review_comments_for_repo  
  *description*: Lists review comments for all pull requests in a repository. By default, review comments are in ascending order by ID.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/pulls/comments/{comment_id}_ 
  *resource*: pullsget_review_comment  
  *description*: Provides details for a specified review comment.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/pulls/{pull_number}/comments_ 
  *resource*: pullslist_review_comments  
  *description*: Lists all review comments for a specified pull request. By default, review comments are in ascending order by ID.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /repos/{owner}/{repo}/commits/{commit_sha}/pulls_ 
  *resource*: reposlist_pull_requests_associated_with_commit  
  *description*: Lists the merged pull request that introduced the commit to the repository. If the commit is not present in the default branch, will only return open pull requests associated with the commit.  To list the open or merged pull requests associated with a branch, you can set the `commit_sha` parameter to the branch name.
* _GET /repos/{owner}/{repo}/pulls_ 
  *resource*: pullslist  
  *description*: Lists pull requests in a specified repository.  Draft pull requests are available in public repositories with GitHub Free and GitHub Free for organizations, GitHub Pro, and legacy per-repository billing plans, and in public and private repositories with GitHub Team and GitHub Enterprise Cloud. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /rate_limit_ 
  *resource*: rate_limitget  
  *description*: > [!NOTE] > Accessing this endpoint does not count against your REST API rate limit.  Some categories of endpoints have custom rate limits that are separate from the rate limit governing the other REST API endpoints. For this reason, the API response categorizes your rate limit. Under `resources`, you'll see objects relating to different categories: * The `core` object provides your rate limit status for all non-search-related resources in the REST API. * The `search` object provides your rate limit status for the REST API for searching (excluding code searches). For more information, see "[Search](https://docs.github.com/rest/search/search)." * The `code_search` object provides your rate limit status for the REST API for searching code. For more information, see "[Search code](https://docs.github.com/rest/search/search#search-code)." * The `graphql` object provides your rate limit status for the GraphQL API. For more information, see "[Resource limitations](https://docs.github.com/graphql/overview/resource-limitations#rate-limit)." * The `integration_manifest` object provides your rate limit status for the `POST /app-manifests/{code}/conversions` operation. For more information, see "[Creating a GitHub App from a manifest](https://docs.github.com/apps/creating-github-apps/setting-up-a-github-app/creating-a-github-app-from-a-manifest#3-you-exchange-the-temporary-code-to-retrieve-the-app-configuration)." * The `dependency_snapshots` object provides your rate limit status for submitting snapshots to the dependency graph. For more information, see "[Dependency graph](https://docs.github.com/rest/dependency-graph)." * The `code_scanning_upload` object provides your rate limit status for uploading SARIF results to code scanning. For more information, see "[Uploading a SARIF file to GitHub](https://docs.github.com/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github)." * The `actions_runner_registration` object provides your rate limit status for registering self-hosted runners in GitHub Actions. For more information, see "[Self-hosted runners](https://docs.github.com/rest/actions/self-hosted-runners)." * The `source_import` object is no longer in use for any API endpoints, and it will be removed in the next API version. For more information about API versions, see "[API Versions](https://docs.github.com/rest/about-the-rest-api/api-versions)."  > [!NOTE] > The `rate` object is deprecated. If you're writing new API client code or updating existing code, you should use the `core` object instead of the `rate` object. The `core` object contains the same information that is present in the `rate` object.
* _GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}/reactions_ 
  *resource*: reactionslist_for_team_discussion_comment_in_org  
  *description*: List the reactions to a [team discussion comment](https://docs.github.com/rest/teams/discussion-comments#get-a-discussion-comment).  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/:org_id/team/:team_id/discussions/:discussion_number/comments/:comment_number/reactions`.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/reactions_ 
  *resource*: reactionslist_for_team_discussion_in_org  
  *description*: List the reactions to a [team discussion](https://docs.github.com/rest/teams/discussions#get-a-discussion).  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/:org_id/team/:team_id/discussions/:discussion_number/reactions`.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/comments/{comment_id}/reactions_ 
  *resource*: reactionslist_for_commit_comment  
  *description*: List the reactions to a [commit comment](https://docs.github.com/rest/commits/comments#get-a-commit-comment).
* _GET /repos/{owner}/{repo}/issues/comments/{comment_id}/reactions_ 
  *resource*: reactionslist_for_issue_comment  
  *description*: List the reactions to an [issue comment](https://docs.github.com/rest/issues/comments#get-an-issue-comment).
* _GET /repos/{owner}/{repo}/issues/{issue_number}/reactions_ 
  *resource*: reactionslist_for_issue  
  *description*: List the reactions to an [issue](https://docs.github.com/rest/issues/issues#get-an-issue).
* _GET /repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions_ 
  *resource*: reactionslist_for_pull_request_review_comment  
  *description*: List the reactions to a [pull request review comment](https://docs.github.com/rest/pulls/comments#get-a-review-comment-for-a-pull-request).
* _GET /repos/{owner}/{repo}/releases/{release_id}/reactions_ 
  *resource*: reactionslist_for_release  
  *description*: List the reactions to a [release](https://docs.github.com/rest/releases/releases#get-a-release).
* _GET /teams/{team_id}/discussions/{discussion_number}/comments/{comment_number}/reactions_ 
  *resource*: reactionslist_for_team_discussion_comment_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [`List reactions for a team discussion comment`](https://docs.github.com/rest/reactions/reactions#list-reactions-for-a-team-discussion-comment) endpoint.  List the reactions to a [team discussion comment](https://docs.github.com/rest/teams/discussion-comments#get-a-discussion-comment).  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /teams/{team_id}/discussions/{discussion_number}/reactions_ 
  *resource*: reactionslist_for_team_discussion_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [`List reactions for a team discussion`](https://docs.github.com/rest/reactions/reactions#list-reactions-for-a-team-discussion) endpoint.  List the reactions to a [team discussion](https://docs.github.com/rest/teams/discussions#get-a-discussion).  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/traffic/popular/referrers_ 
  *resource*: reposget_top_referrers  
  *description*: Get the top 10 referrers over the last 14 days.
* _GET /repos/{owner}/{repo}/releases_ 
  *resource*: reposlist_releases  
  *description*: This returns a list of releases, which does not include regular Git tags that have not been associated with a release. To get a list of Git tags, use the [Repository Tags API](https://docs.github.com/rest/repos/repos#list-repository-tags).  Information about published releases are available to everyone. Only users with push access will receive listings for draft releases.
* _GET /repos/{owner}/{repo}/releases/tags/{tag}_ 
  *resource*: reposget_release_by_tag  
  *description*: Get a published release with the specified tag.
* _GET /repos/{owner}/{repo}/releases/{release_id}_ 
  *resource*: reposget_release  
  *description*: Gets a public release with the specified release ID.  > [!NOTE] > This returns an `upload_url` key corresponding to the endpoint for uploading release assets. This key is a hypermedia resource. For more information, see "[Getting started with the REST API](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#hypermedia)."
* _GET /repos/{owner}/{repo}/releases/assets/{asset_id}_ 
  *resource*: reposget_release_asset  
  *description*: To download the asset's binary content, set the `Accept` header of the request to [`application/octet-stream`](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types). The API will either redirect the client to the location, or stream it directly if possible. API clients should handle both a `200` or `302` response.
* _GET /repos/{owner}/{repo}/releases/latest_ 
  *resource*: reposget_latest_release  
  *description*: View the latest published full release for the repository.  The latest release is the most recent non-prerelease, non-draft release, sorted by the `created_at` attribute. The `created_at` attribute is the date of the commit used for the release, and not the date when the release was drafted or published.
* _GET /repos/{owner}/{repo}/releases/{release_id}/assets_ 
  *resource*: reposlist_release_assets  
* _GET /repos/{owner}/{repo}/codespaces/secrets_ 
  *resource*: codespaceslist_repo_secrets  
  *description*: Lists all development environment secrets available in a repository without revealing their encrypted values.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/codespaces/secrets/{secret_name}_ 
  *resource*: codespacesget_repo_secret  
  *description*: Gets a single repository development environment secret without revealing its encrypted value.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /search/repositories_ 
  *resource*: searchrepos  
  *description*: Find repositories via various criteria. This method returns up to 100 results [per page](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api).  When searching for repositories, you can get text match metadata for the **name** and **description** fields when you pass the `text-match` media type. For more details about how to receive highlighted search results, see [Text match metadata](https://docs.github.com/rest/search/search#text-match-metadata).  For example, if you want to search for popular Tetris repositories written in assembly code, your query might look like this:  `q=tetris+language:assembly&sort=stars&order=desc`  This query searches for repositories with the word `tetris` in the name, the description, or the README. The results are limited to repositories where the primary language is assembly. The results are sorted by stars in descending order, so that the most popular repositories appear first in the search results.
* _GET /installation/repositories_ 
  *resource*: appslist_repos_accessible_to_installation  
  *description*: List repositories that an app installation can access.
* _GET /orgs/{org}/actions/permissions/repositories_ 
  *resource*: actionslist_selected_repositories_enabled_github_actions_organization  
  *description*: Lists the selected repositories that are enabled for GitHub Actions in an organization. To use this endpoint, the organization permission policy for `enabled_repositories` must be configured to `selected`. For more information, see "[Set GitHub Actions permissions for an organization](#set-github-actions-permissions-for-an-organization)."  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /user/installations/{installation_id}/repositories_ 
  *resource*: appslist_installation_repos_for_authenticated_user  
  *description*: List repositories that the authenticated user has explicit permission (`:read`, `:write`, or `:admin`) to access for an installation.  The authenticated user has explicit permission to access repositories they own, repositories where they are a collaborator, and repositories that they can access through an organization membership.  The access the user has to each repository is included in the hash under the `permissions` key.
* _GET /user/repos_ 
  *resource*: reposlist_for_authenticated_user  
  *description*: Lists repositories that the authenticated user has explicit permission (`:read`, `:write`, or `:admin`) to access.  The authenticated user has explicit permission to access repositories they own, repositories where they are a collaborator, and repositories that they can access through an organization membership.
* _GET /user/starred_ 
  *resource*: activitylist_repos_starred_by_authenticated_user  
  *description*: Lists repositories the authenticated user has starred.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.star+json`**: Includes a timestamp of when the star was created.
* _GET /orgs/{org}/security-advisories_ 
  *resource*: security_advisorieslist_org_repository_advisories  
  *description*: Lists repository security advisories for an organization.  The authenticated user must be an owner or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` or `repository_advisories:write` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/security-advisories_ 
  *resource*: security_advisorieslist_repository_advisories  
  *description*: Lists security advisories in a repository.  The authenticated user can access unpublished security advisories from a repository if they are a security manager or administrator of that repository, or if they are a collaborator on any security advisory.  OAuth app tokens and personal access tokens (classic) need the `repo` or `repository_advisories:read` scope to to get a published security advisory in a private repository, or any unpublished security advisory that the authenticated user has access to.
* _GET /repos/{owner}/{repo}/security-advisories/{ghsa_id}_ 
  *resource*: security_advisoriesget_repository_advisory  
  *description*: Get a repository security advisory using its GitHub Security Advisory (GHSA) identifier.  Anyone can access any published security advisory on a public repository.  The authenticated user can access an unpublished security advisory from a repository if they are a security manager or administrator of that repository, or if they are a collaborator on the security advisory.  OAuth app tokens and personal access tokens (classic) need the `repo` or `repository_advisories:read` scope to to get a published security advisory in a private repository, or any unpublished security advisory that the authenticated user has access to.
* _GET /repos/{owner}/{repo}/collaborators/{username}/permission_ 
  *resource*: reposget_collaborator_permission_level  
  *description*: Checks the repository permission of a collaborator. The possible repository permissions are `admin`, `write`, `read`, and `none`.  *Note*: The `permission` attribute provides the legacy base roles of `admin`, `write`, `read`, and `none`, where the `maintain` role is mapped to `write` and the `triage` role is mapped to `read`. To determine the role assigned to the collaborator, see the `role_name` attribute, which will provide the full role name, including custom roles. The `permissions` hash can also be used to determine which base level of access the collaborator has to the repository.
* _GET /repos/{owner}/{repo}/invitations_ 
  *resource*: reposlist_invitations  
  *description*: When authenticating as a user with admin rights to a repository, this endpoint will list all currently open repository invitations.
* _GET /user/repository_invitations_ 
  *resource*: reposlist_invitations_for_authenticated_user  
  *description*: When authenticating as a user, this endpoint will list all currently open repository invitations for that user.
* _GET /repos/{owner}/{repo}/rules/branches/{branch}_ 
  *resource*: reposget_branch_rules  
  *description*: Returns all active rules that apply to the specified branch. The branch does not need to exist; rules that would apply to a branch with that name will be returned. All active rules that apply will be returned, regardless of the level at which they are configured (e.g. repository or organization). Rules in rulesets with "evaluate" or "disabled" enforcement statuses are not returned.
* _GET /orgs/{org}/rulesets_ 
  *resource*: reposget_org_rulesets  
  *description*: Get all the repository rulesets for an organization.
* _GET /orgs/{org}/rulesets/{ruleset_id}_ 
  *resource*: reposget_org_ruleset  
  *description*: Get a repository ruleset for an organization.
* _GET /repos/{owner}/{repo}/rulesets_ 
  *resource*: reposget_repo_rulesets  
  *description*: Get all the rulesets for a repository.
* _GET /repos/{owner}/{repo}/rulesets/{ruleset_id}_ 
  *resource*: reposget_repo_ruleset  
  *description*: Get a ruleset for a repository.
* _GET /repos/{owner}/{repo}/subscription_ 
  *resource*: activityget_repo_subscription  
  *description*: Gets information about whether the authenticated user is subscribed to the repository.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks_ 
  *resource*: reposget_status_checks_protection  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/restrictions_ 
  *resource*: reposget_access_restrictions  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.  Lists who has access to this protected branch.  > [!NOTE] > Users, apps, and teams `restrictions` are only available for organization-owned repositories.
* _GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/comments_ 
  *resource*: pullslist_comments_for_review  
  *description*: Lists comments for a specific pull request review.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github-commitcomment.raw+json`**: Returns the raw markdown body. Response will include `body`. This is the default if you do not pass any specific media type. - **`application/vnd.github-commitcomment.text+json`**: Returns a text only representation of the markdown body. Response will include `body_text`. - **`application/vnd.github-commitcomment.html+json`**: Returns HTML rendered from the body's markdown. Response will include `body_html`. - **`application/vnd.github-commitcomment.full+json`**: Returns raw, text, and HTML representations. Response will include `body`, `body_text`, and `body_html`.
* _GET /_ 
  *resource*: metaroot  
  *description*: Get Hypermedia links to resources accessible in GitHub's REST API
* _GET /orgs/{org}/rulesets/rule-suites_ 
  *resource*: reposget_org_rule_suites  
  *description*: Lists suites of rule evaluations at the organization level. For more information, see "[Managing rulesets for repositories in your organization](https://docs.github.com/organizations/managing-organization-settings/managing-rulesets-for-repositories-in-your-organization#viewing-insights-for-rulesets)."
* _GET /orgs/{org}/rulesets/rule-suites/{rule_suite_id}_ 
  *resource*: reposget_org_rule_suite  
  *description*: Gets information about a suite of rule evaluations from within an organization. For more information, see "[Managing rulesets for repositories in your organization](https://docs.github.com/organizations/managing-organization-settings/managing-rulesets-for-repositories-in-your-organization#viewing-insights-for-rulesets)."
* _GET /repos/{owner}/{repo}/rulesets/rule-suites_ 
  *resource*: reposget_repo_rule_suites  
  *description*: Lists suites of rule evaluations at the repository level. For more information, see "[Managing rulesets for a repository](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository#viewing-insights-for-rulesets)."
* _GET /repos/{owner}/{repo}/rulesets/rule-suites/{rule_suite_id}_ 
  *resource*: reposget_repo_rule_suite  
  *description*: Gets information about a suite of rule evaluations from within a repository. For more information, see "[Managing rulesets for a repository](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository#viewing-insights-for-rulesets)."
* _GET /orgs/{org}/actions/runners_ 
  *resource*: actionslist_self_hosted_runners_for_org  
  *description*: Lists all self-hosted runners configured in an organization.  Authenticated users must have admin access to the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint. If the repository is private, the `repo` scope is also required.
* _GET /orgs/{org}/actions/runners/{runner_id}_ 
  *resource*: actionsget_self_hosted_runner_for_org  
  *description*: Gets a specific self-hosted runner configured in an organization.  Authenticated users must have admin access to the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint. If the repository is private, the `repo` scope is also required.
* _GET /repos/{owner}/{repo}/actions/runners_ 
  *resource*: actionslist_self_hosted_runners_for_repo  
  *description*: Lists all self-hosted runners configured in a repository.  Authenticated users must have admin access to the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/runners/{runner_id}_ 
  *resource*: actionsget_self_hosted_runner_for_repo  
  *description*: Gets a specific self-hosted runner configured in a repository.  Authenticated users must have admin access to the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /orgs/{org}/actions/runners/downloads_ 
  *resource*: actionslist_runner_applications_for_org  
  *description*: Lists binaries for the runner application that you can download and run.  Authenticated users must have admin access to the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.  If the repository is private, the `repo` scope is also required.
* _GET /repos/{owner}/{repo}/actions/runners/downloads_ 
  *resource*: actionslist_runner_applications_for_repo  
  *description*: Lists binaries for the runner application that you can download and run.  Authenticated users must have admin access to the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /orgs/{org}/actions/runners/{runner_id}/labels_ 
  *resource*: actionslist_labels_for_self_hosted_runner_for_org  
  *description*: Lists all labels for a self-hosted runner configured in an organization.  Authenticated users must have admin access to the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint. If the repository is private, the `repo` scope is also required.
* _GET /repos/{owner}/{repo}/actions/runners/{runner_id}/labels_ 
  *resource*: actionslist_labels_for_self_hosted_runner_for_repo  
  *description*: Lists all labels for a self-hosted runner configured in a repository.  Authenticated users must have admin access to the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/dependency-graph/sbom_ 
  *resource*: dependency_graphexport_sbom  
  *description*: Exports the software bill of materials (SBOM) for a repository in SPDX JSON format.
* _GET /repos/{owner}/{repo}/secret-scanning/alerts_ 
  *resource*: secret_scanninglist_alerts_for_repo  
  *description*: Lists secret scanning alerts for an eligible repository, from newest to oldest.  The authenticated user must be an administrator for the repository or for the organization that owns the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` or `security_events` scope to use this endpoint. If this endpoint is only used with public repositories, the token can use the `public_repo` scope instead.
* _GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}_ 
  *resource*: secret_scanningget_alert  
  *description*: Gets a single secret scanning alert detected in an eligible repository.  The authenticated user must be an administrator for the repository or for the organization that owns the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` or `security_events` scope to use this endpoint. If this endpoint is only used with public repositories, the token can use the `public_repo` scope instead.
* _GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}/locations_ 
  *resource*: secret_scanninglist_locations_for_alert  
  *description*: Lists all locations for a given secret scanning alert for an eligible repository.  The authenticated user must be an administrator for the repository or for the organization that owns the repository to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` or `security_events` scope to use this endpoint. If this endpoint is only used with public repositories, the token can use the `public_repo` scope instead.
* _GET /orgs/{org}/actions/permissions/selected-actions_ 
  *resource*: actionsget_allowed_actions_organization  
  *description*: Gets the selected actions and reusable workflows that are allowed in an organization. To use this endpoint, the organization permission policy for `allowed_actions` must be configured to `selected`. For more information, see "[Set GitHub Actions permissions for an organization](#set-github-actions-permissions-for-an-organization)."  OAuth tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/permissions/selected-actions_ 
  *resource*: actionsget_allowed_actions_repository  
  *description*: Gets the settings for selected actions and reusable workflows that are allowed in a repository. To use this endpoint, the repository policy for `allowed_actions` must be configured to `selected`. For more information, see "[Set GitHub Actions permissions for a repository](#set-github-actions-permissions-for-a-repository)."  OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/branches_ 
  *resource*: reposlist_branches  
* _GET /classrooms_ 
  *resource*: classroomlist_classrooms  
  *description*: Lists GitHub Classroom classrooms for the current user. Classrooms will only be returned if the current user is an administrator of one or more GitHub Classrooms.
* _GET /classrooms/{classroom_id}/assignments_ 
  *resource*: classroomlist_assignments_for_a_classroom  
  *description*: Lists GitHub Classroom assignments for a classroom. Assignments will only be returned if the current user is an administrator of the GitHub Classroom.
* _GET /repos/{owner}/{repo}/commits/{ref}/status_ 
  *resource*: reposget_combined_status_for_ref  
  *description*: Users with pull access in a repository can access a combined view of commit statuses for a given ref. The ref can be a SHA, a branch name, or a tag name.   Additionally, a combined `state` is returned. The `state` is one of:  *   **failure** if any of the contexts report as `error` or `failure` *   **pending** if there are no statuses or a context is `pending` *   **success** if the latest status for all contexts is `success`
* _GET /orgs/{org}/blocks_ 
  *resource*: orgslist_blocked_users  
  *description*: List the users blocked by an organization.
* _GET /orgs/{org}/members_ 
  *resource*: orgslist_members  
  *description*: List all users who are members of an organization. If the authenticated user is also a member of this organization then both concealed and public members will be returned.
* _GET /orgs/{org}/outside_collaborators_ 
  *resource*: orgslist_outside_collaborators  
  *description*: List all users who are outside collaborators of an organization.
* _GET /orgs/{org}/public_members_ 
  *resource*: orgslist_public_members  
  *description*: Members of an organization can choose to have their membership publicized or not.
* _GET /orgs/{org}/teams/{team_slug}/members_ 
  *resource*: teamslist_members_in_org  
  *description*: Team members will include the members of child teams.  To list members in a team, the team must be visible to the authenticated user.
* _GET /projects/{project_id}/collaborators_ 
  *resource*: projectslist_collaborators  
  *description*: Lists the collaborators for an organization project. For a project, the list of collaborators includes outside collaborators, organization members that are direct collaborators, organization members with access through team memberships, organization members with access through default organization permissions, and organization owners. You must be an organization owner or a project `admin` to list collaborators.
* _GET /repos/{owner}/{repo}/assignees_ 
  *resource*: issueslist_assignees  
  *description*: Lists the [available assignees](https://docs.github.com/articles/assigning-issues-and-pull-requests-to-other-github-users/) for issues in a repository.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/required_pull_request_reviews_ 
  *resource*: reposget_pull_request_review_protection  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/users_ 
  *resource*: reposget_users_with_access_to_protected_branch  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.  Lists the people who have push access to this branch.
* _GET /repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers_ 
  *resource*: pullslist_requested_reviewers  
  *description*: Gets the users or teams whose review is requested for a pull request. Once a requested reviewer submits a review, they are no longer considered a requested reviewer. Their review will instead be returned by the [List reviews for a pull request](https://docs.github.com/rest/pulls/reviews#list-reviews-for-a-pull-request) operation.
* _GET /repos/{owner}/{repo}/subscribers_ 
  *resource*: activitylist_watchers_for_repo  
  *description*: Lists the people watching the specified repository.
* _GET /teams/{team_id}/members_ 
  *resource*: teamslist_members_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [`List team members`](https://docs.github.com/rest/teams/members#list-team-members) endpoint.  Team members will include the members of child teams.
* _GET /user/blocks_ 
  *resource*: userslist_blocked_by_authenticated_user  
  *description*: List the users you've blocked on your personal account.
* _GET /user/followers_ 
  *resource*: userslist_followers_for_authenticated_user  
  *description*: Lists the people following the authenticated user.
* _GET /user/following_ 
  *resource*: userslist_followed_by_authenticated_user  
  *description*: Lists the people who the authenticated user follows.
* _GET /users_ 
  *resource*: userslist  
  *description*: Lists all users, in the order that they signed up on GitHub. This list includes personal user accounts and organization accounts.  Note: Pagination is powered exclusively by the `since` parameter. Use the [Link header](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api#using-link-headers) to get the URL for the next page of users.
* _GET /users/{username}/followers_ 
  *resource*: userslist_followers_for_user  
  *description*: Lists the people following the specified user.
* _GET /users/{username}/following_ 
  *resource*: userslist_following_for_user  
  *description*: Lists the people who the specified user follows.
* _GET /user/social_accounts_ 
  *resource*: userslist_social_accounts_for_authenticated_user  
  *description*: Lists all of your social accounts.
* _GET /users/{username}/social_accounts_ 
  *resource*: userslist_social_accounts_for_user  
  *description*: Lists social media accounts for a user. This endpoint is accessible by anyone.
* _GET /user/ssh_signing_keys_ 
  *resource*: userslist_ssh_signing_keys_for_authenticated_user  
  *description*: Lists the SSH signing keys for the authenticated user's GitHub account.  OAuth app tokens and personal access tokens (classic) need the `read:ssh_signing_key` scope to use this endpoint.
* _GET /user/ssh_signing_keys/{ssh_signing_key_id}_ 
  *resource*: usersget_ssh_signing_key_for_authenticated_user  
  *description*: Gets extended details for an SSH signing key.  OAuth app tokens and personal access tokens (classic) need the `read:ssh_signing_key` scope to use this endpoint.
* _GET /users/{username}/ssh_signing_keys_ 
  *resource*: userslist_ssh_signing_keys_for_user  
  *description*: Lists the SSH signing keys for a user. This operation is accessible by anyone.
* _GET /gists/{gist_id}/star_ 
  *resource*: gistscheck_is_starred  
* _GET /repos/{owner}/{repo}/stargazers_ 
  *resource*: activitylist_stargazers_for_repo  
  *description*: Lists the people that have starred the repository.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.star+json`**: Includes a timestamp of when the star was created.
* _GET /user/starred/{owner}/{repo}_ 
  *resource*: activitycheck_repo_is_starred_by_authenticated_user  
  *description*: Whether the authenticated user has starred the repository.
* _GET /users/{username}/starred_ 
  *resource*: activitylist_repos_starred_by_user  
  *description*: Lists repositories a user has starred.  This endpoint supports the following custom media types. For more information, see "[Media types](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types)."  - **`application/vnd.github.star+json`**: Includes a timestamp of when the star was created.
* _GET /repos/{owner}/{repo}/commits/{ref}/statuses_ 
  *resource*: reposlist_commit_statuses_for_ref  
  *description*: Users with pull access in a repository can view commit statuses for a given ref. The ref can be a SHA, a branch name, or a tag name. Statuses are returned in reverse chronological order. The first status in the list will be the latest one.  This resource is also available via a legacy route: `GET /repos/:owner/:repo/statuses/:ref`.
* _GET /orgs/{org}/actions/oidc/customization/sub_ 
  *resource*: oidcget_oidc_custom_sub_template_for_org  
  *description*: Gets the customization template for an OpenID Connect (OIDC) subject claim.  OAuth app tokens and personal access tokens (classic) need the `read:org` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/oidc/customization/sub_ 
  *resource*: actionsget_custom_oidc_sub_claim_for_repo  
  *description*: Gets the customization template for an OpenID Connect (OIDC) subject claim.  OAuth tokens and personal access tokens (classic) need the `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/tags_ 
  *resource*: reposlist_tags  
* _GET /repos/{owner}/{repo}/tags/protection_ 
  *resource*: reposlist_tag_protection  
  *description*: > [!WARNING] > **Deprecation notice:** This operation is deprecated and will be removed after August 30, 2024. Use the "[Repository Rulesets](https://docs.github.com/rest/repos/rules#get-all-repository-rulesets)" endpoint instead.  This returns the tag protection states of a repository.  This information is only available to repository administrators.
* _GET /repos/{owner}/{repo}/tarball/{ref}_ 
  *resource*: reposdownload_tarball_archive  
  *description*: Gets a redirect URL to download a tar archive for a repository. If you omit `:ref`, the repository’s default branch (usually `main`) will be used. Please make sure your HTTP framework is configured to follow redirects or you will need to use the `Location` header to make a second `GET` request.  > [!NOTE] > For private repositories, these links are temporary and expire after five minutes.
* _GET /orgs/{org}/invitations/{invitation_id}/teams_ 
  *resource*: orgslist_invitation_teams  
  *description*: List all teams associated with an invitation. In order to see invitations in an organization, the authenticated user must be an organization owner.
* _GET /orgs/{org}/teams_ 
  *resource*: teamslist  
  *description*: Lists all teams in an organization that are visible to the authenticated user.
* _GET /orgs/{org}/teams/{team_slug}/teams_ 
  *resource*: teamslist_child_in_org  
  *description*: Lists the child teams of the team specified by `{team_slug}`.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/teams`.
* _GET /repos/{owner}/{repo}/branches/{branch}/protection/restrictions/teams_ 
  *resource*: reposget_teams_with_access_to_protected_branch  
  *description*: Protected branches are available in public repositories with GitHub Free and GitHub Free for organizations, and in public and private repositories with GitHub Pro, GitHub Team, GitHub Enterprise Cloud, and GitHub Enterprise Server. For more information, see [GitHub's products](https://docs.github.com/github/getting-started-with-github/githubs-products) in the GitHub Help documentation.  Lists the teams who have push access to this branch. The list includes child teams.
* _GET /repos/{owner}/{repo}/teams_ 
  *resource*: reposlist_teams  
  *description*: Lists the teams that have access to the specified repository and that are also visible to the authenticated user.  For a public repository, a team is listed only if that team added the public repository explicitly.  OAuth app tokens and personal access tokens (classic) need the `public_repo` or `repo` scope to use this endpoint with a public repository, and `repo` scope to use this endpoint with a private repository.
* _GET /teams/{team_id}/teams_ 
  *resource*: teamslist_child_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [`List child teams`](https://docs.github.com/rest/teams/teams#list-child-teams) endpoint.
* _GET /orgs/{org}/teams/{team_slug}/discussions_ 
  *resource*: teamslist_discussions_in_org  
  *description*: List all discussions on a team's page.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/discussions`.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}_ 
  *resource*: teamsget_discussion_in_org  
  *description*: Get a specific discussion on a team's page.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/discussions/{discussion_number}`.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /teams/{team_id}/discussions_ 
  *resource*: teamslist_discussions_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [`List discussions`](https://docs.github.com/rest/teams/discussions#list-discussions) endpoint.  List all discussions on a team's page.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /teams/{team_id}/discussions/{discussion_number}_ 
  *resource*: teamsget_discussion_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [Get a discussion](https://docs.github.com/rest/teams/discussions#get-a-discussion) endpoint.  Get a specific discussion on a team's page.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments_ 
  *resource*: teamslist_discussion_comments_in_org  
  *description*: List all comments on a team discussion.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/discussions/{discussion_number}/comments`.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /orgs/{org}/teams/{team_slug}/discussions/{discussion_number}/comments/{comment_number}_ 
  *resource*: teamsget_discussion_comment_in_org  
  *description*: Get a specific comment on a team discussion.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/discussions/{discussion_number}/comments/{comment_number}`.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /teams/{team_id}/discussions/{discussion_number}/comments_ 
  *resource*: teamslist_discussion_comments_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [List discussion comments](https://docs.github.com/rest/teams/discussion-comments#list-discussion-comments) endpoint.  List all comments on a team discussion.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /teams/{team_id}/discussions/{discussion_number}/comments/{comment_number}_ 
  *resource*: teamsget_discussion_comment_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [Get a discussion comment](https://docs.github.com/rest/teams/discussion-comments#get-a-discussion-comment) endpoint.  Get a specific comment on a team discussion.  OAuth app tokens and personal access tokens (classic) need the `read:discussion` scope to use this endpoint.
* _GET /orgs/{org}/teams/{team_slug}_ 
  *resource*: teamsget_by_name  
  *description*: Gets a team using the team's `slug`. To create the `slug`, GitHub replaces special characters in the `name` string, changes all words to lowercase, and replaces spaces with a `-` separator. For example, `"My TEam Näme"` would become `my-team-name`.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}`.
* _GET /teams/{team_id}_ 
  *resource*: teamsget_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the [Get a team by name](https://docs.github.com/rest/teams/teams#get-a-team-by-name) endpoint.
* _GET /user/teams_ 
  *resource*: teamslist_for_authenticated_user  
  *description*: List all of the teams across all of the organizations to which the authenticated user belongs.  OAuth app tokens and personal access tokens (classic) need the `user`, `repo`, or `read:org` scope to use this endpoint.  When using a fine-grained personal access token, the resource owner of the token must be a single organization, and the response will only include the teams from that organization.
* _GET /orgs/{org}/teams/{team_slug}/memberships/{username}_ 
  *resource*: teamsget_membership_for_user_in_org  
  *description*: Team members will include the members of child teams.  To get a user's membership with a team, the team must be visible to the authenticated user.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/memberships/{username}`.  > [!NOTE] > The response contains the `state` of the membership and the member's `role`.  The `role` for organization owners is set to `maintainer`. For more information about `maintainer` roles, see [Create a team](https://docs.github.com/rest/teams/teams#create-a-team).
* _GET /teams/{team_id}/memberships/{username}_ 
  *resource*: teamsget_membership_for_user_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [Get team membership for a user](https://docs.github.com/rest/teams/members#get-team-membership-for-a-user) endpoint.  Team members will include the members of child teams.  To get a user's membership with a team, the team must be visible to the authenticated user.  **Note:** The response contains the `state` of the membership and the member's `role`.  The `role` for organization owners is set to `maintainer`. For more information about `maintainer` roles, see [Create a team](https://docs.github.com/rest/teams/teams#create-a-team).
* _GET /orgs/{org}/teams/{team_slug}/projects_ 
  *resource*: teamslist_projects_in_org  
  *description*: Lists the organization projects for a team.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/projects`.
* _GET /orgs/{org}/teams/{team_slug}/projects/{project_id}_ 
  *resource*: teamscheck_permissions_for_project_in_org  
  *description*: Checks whether a team has `read`, `write`, or `admin` permissions for an organization project. The response includes projects inherited from a parent team.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/projects/{project_id}`.
* _GET /teams/{team_id}/projects_ 
  *resource*: teamslist_projects_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [`List team projects`](https://docs.github.com/rest/teams/teams#list-team-projects) endpoint.  Lists the organization projects for a team.
* _GET /teams/{team_id}/projects/{project_id}_ 
  *resource*: teamscheck_permissions_for_project_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [Check team permissions for a project](https://docs.github.com/rest/teams/teams#check-team-permissions-for-a-project) endpoint.  Checks whether a team has `read`, `write`, or `admin` permissions for an organization project. The response includes projects inherited from a parent team.
* _GET /orgs/{org}/teams/{team_slug}/repos/{owner}/{repo}_ 
  *resource*: teamscheck_permissions_for_repo_in_org  
  *description*: Checks whether a team has `admin`, `push`, `maintain`, `triage`, or `pull` permission for a repository. Repositories inherited through a parent team will also be checked.  You can also get information about the specified repository, including what permissions the team grants on it, by passing the following custom [media type](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types/) via the `application/vnd.github.v3.repository+json` accept header.  If a team doesn't have permission for the repository, you will receive a `404 Not Found` response status.  If the repository is private, you must have at least `read` permission for that repository, and your token must have the `repo` or `admin:org` scope. Otherwise, you will receive a `404 Not Found` response status.  > [!NOTE] > You can also specify a team by `org_id` and `team_id` using the route `GET /organizations/{org_id}/team/{team_id}/repos/{owner}/{repo}`.
* _GET /teams/{team_id}/repos/{owner}/{repo}_ 
  *resource*: teamscheck_permissions_for_repo_legacy  
  *description*: > [!WARNING] > **Deprecation notice:** This endpoint route is deprecated and will be removed from the Teams API. We recommend migrating your existing code to use the new [Check team permissions for a repository](https://docs.github.com/rest/teams/teams#check-team-permissions-for-a-repository) endpoint.  > [!NOTE] > Repositories inherited through a parent team will also be checked.  You can also get information about the specified repository, including what permissions the team grants on it, by passing the following custom [media type](https://docs.github.com/rest/using-the-rest-api/getting-started-with-the-rest-api#media-types/) via the `Accept` header:
* _GET /orgs/{org}/organization-roles/{role_id}/teams_ 
  *resource*: orgslist_org_role_teams  
  *description*: Lists the teams that are assigned to an organization role. For more information on organization roles, see "[Using organization roles](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/using-organization-roles)."  To use this endpoint, you must be an administrator for the organization.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /orgs/{org}/security-managers_ 
  *resource*: orgslist_security_manager_teams  
  *description*: Lists teams that are security managers for an organization. For more information, see "[Managing security managers in your organization](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization)."  The authenticated user must be an administrator or security manager for the organization to use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `read:org` scope to use this endpoint.
* _GET /gitignore/templates_ 
  *resource*: gitignoreget_all_templates  
  *description*: List all templates available to pass as an option when [creating a repository](https://docs.github.com/rest/repos/repos#create-a-repository-for-the-authenticated-user).
* _GET /notifications_ 
  *resource*: activitylist_notifications_for_authenticated_user  
  *description*: List all notifications for the current user, sorted by most recently updated.
* _GET /notifications/threads/{thread_id}_ 
  *resource*: activityget_thread  
  *description*: Gets information about a notification thread.
* _GET /repos/{owner}/{repo}/notifications_ 
  *resource*: activitylist_repo_notifications_for_authenticated_user  
  *description*: Lists all notifications for the current user in the specified repository.
* _GET /notifications/threads/{thread_id}/subscription_ 
  *resource*: activityget_thread_subscription_for_authenticated_user  
  *description*: This checks to see if the current user is subscribed to a thread. You can also [get a repository subscription](https://docs.github.com/rest/activity/watching#get-a-repository-subscription).  Note that subscriptions are only generated if a user is participating in a conversation--for example, they've replied to the thread, were **@mentioned**, or manually subscribe to a thread.
* _GET /repos/{owner}/{repo}/issues/{issue_number}/timeline_ 
  *resource*: issueslist_events_for_timeline  
  *description*: List all timeline events for an issue.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/timing_ 
  *resource*: actionsget_workflow_run_usage  
  *description*: Gets the number of billable minutes and total run time for a specific workflow run. Billable minutes only apply to workflows in private repositories that use GitHub-hosted runners. Usage is listed for each GitHub-hosted runner operating system in milliseconds. Any job re-runs are also included in the usage. The usage does not include the multiplier for macOS and Windows runners and is not rounded up to the nearest whole minute. For more information, see "[Managing billing for GitHub Actions](https://docs.github.com/github/setting-up-and-managing-billing-and-payments-on-github/managing-billing-for-github-actions)".  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/timing_ 
  *resource*: actionsget_workflow_usage  
  *description*: Gets the number of billable minutes used by a specific workflow during the current billing cycle. Billable minutes only apply to workflows in private repositories that use GitHub-hosted runners. Usage is listed for each GitHub-hosted runner operating system in milliseconds. Any job re-runs are also included in the usage. The usage does not include the multiplier for macOS and Windows runners and is not rounded up to the nearest whole minute. For more information, see "[Managing billing for GitHub Actions](https://docs.github.com/github/setting-up-and-managing-billing-and-payments-on-github/managing-billing-for-github-actions)".  You can replace `workflow_id` with the workflow file name. For example, you could use `main.yaml`.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/topics_ 
  *resource*: reposget_all_topics  
* _GET /search/topics_ 
  *resource*: searchtopics  
  *description*: Find topics via various criteria. Results are sorted by best match. This method returns up to 100 results [per page](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api). See "[Searching topics](https://docs.github.com/articles/searching-topics/)" for a detailed list of qualifiers.  When searching for topics, you can get text match metadata for the topic's **short\_description**, **description**, **name**, or **display\_name** field when you pass the `text-match` media type. For more details about how to receive highlighted search results, see [Text match metadata](https://docs.github.com/rest/search/search#text-match-metadata).  For example, if you want to search for topics related to Ruby that are featured on https://github.com/topics. Your query might look like this:  `q=ruby+is:featured`  This query searches for topics with the keyword `ruby` and limits the results to find only topics that are featured. The topics that are the best match for the query appear first in the search results.
* _GET /repos/{owner}/{repo}/traffic/clones_ 
  *resource*: reposget_clones  
  *description*: Get the total number of clones and breakdown per day or week for the last 14 days. Timestamps are aligned to UTC midnight of the beginning of the day or week. Week begins on Monday.
* _GET /repos/{owner}/{repo}/traffic/views_ 
  *resource*: reposget_views  
  *description*: Get the total number of views and breakdown per day or week for the last 14 days. Timestamps are aligned to UTC midnight of the beginning of the day or week. Week begins on Monday.
* _GET /user_ 
  *resource*: usersget_authenticated  
  *description*: OAuth app tokens and personal access tokens (classic) need the `user` scope in order for the response to include private profile information.
* _GET /user/{account_id}_ 
  *resource*: usersget_by_id  
  *description*: Provides publicly available information about someone with a GitHub account. This method takes their durable user `ID` instead of their `login`, which can change over time.  The `email` key in the following response is the publicly visible email address from your GitHub [profile page](https://github.com/settings/profile). When setting up your profile, you can select a primary email address to be “public” which provides an email entry for this endpoint. If you do not set a public email address for `email`, then it will have a value of `null`. You only see publicly visible email addresses when authenticated with GitHub. For more information, see [Authentication](https://docs.github.com/rest/guides/getting-started-with-the-rest-api#authentication).  The Emails API enables you to list all of your email addresses, and toggle a primary email to be visible publicly. For more information, see "[Emails API](https://docs.github.com/rest/users/emails)".
* _GET /users/{username}_ 
  *resource*: usersget_by_username  
  *description*: Provides publicly available information about someone with a GitHub account.  The `email` key in the following response is the publicly visible email address from your GitHub [profile page](https://github.com/settings/profile). When setting up your profile, you can select a primary email address to be “public” which provides an email entry for this endpoint. If you do not set a public email address for `email`, then it will have a value of `null`. You only see publicly visible email addresses when authenticated with GitHub. For more information, see [Authentication](https://docs.github.com/rest/guides/getting-started-with-the-rest-api#authentication).  The Emails API enables you to list all of your email addresses, and toggle a primary email to be visible publicly. For more information, see "[Emails API](https://docs.github.com/rest/users/emails)".
* _GET /user/marketplace_purchases_ 
  *resource*: appslist_subscriptions_for_authenticated_user  
  *description*: Lists the active subscriptions for the authenticated user.
* _GET /user/marketplace_purchases/stubbed_ 
  *resource*: appslist_subscriptions_for_authenticated_user_stubbed  
  *description*: Lists the active subscriptions for the authenticated user.
* _GET /orgs/{org}/organization-roles/{role_id}/users_ 
  *resource*: orgslist_org_role_users  
  *description*: Lists organization members that are assigned to an organization role. For more information on organization roles, see "[Using organization roles](https://docs.github.com/organizations/managing-peoples-access-to-your-organization-with-roles/using-organization-roles)."  To use this endpoint, you must be an administrator for the organization.  OAuth app tokens and personal access tokens (classic) need the `admin:org` scope to use this endpoint.
* _GET /search/users_ 
  *resource*: searchusers  
  *description*: Find users via various criteria. This method returns up to 100 results [per page](https://docs.github.com/rest/guides/using-pagination-in-the-rest-api).  When searching for users, you can get text match metadata for the issue **login**, public **email**, and **name** fields when you pass the `text-match` media type. For more details about highlighting search results, see [Text match metadata](https://docs.github.com/rest/search/search#text-match-metadata). For more details about how to receive highlighted search results, see [Text match metadata](https://docs.github.com/rest/search/search#text-match-metadata).  For example, if you're looking for a list of popular users, you might try this query:  `q=tom+repos:%3E42+followers:%3E1000`  This query searches for users with the name `tom`. The results are restricted to users with more than 42 repositories and over 1,000 followers.  This endpoint does not accept authentication and will only include publicly visible users. As an alternative, you can use the GraphQL API. The GraphQL API requires authentication and will return private users, including Enterprise Managed Users (EMUs), that you are authorized to view. For more information, see "[GraphQL Queries](https://docs.github.com/graphql/reference/queries#search)."
* _GET /versions_ 
  *resource*: metaget_all_versions  
  *description*: Get all supported GitHub API versions.
* _GET /repos/{owner}/{repo}/vulnerability-alerts_ 
  *resource*: reposcheck_vulnerability_alerts  
  *description*: Shows whether dependency alerts are enabled or disabled for a repository. The authenticated user must have admin read access to the repository. For more information, see "[About security alerts for vulnerable dependencies](https://docs.github.com/articles/about-security-alerts-for-vulnerable-dependencies)".
* _GET /app/hook/config_ 
  *resource*: appsget_webhook_config_for_app  
  *description*: Returns the webhook configuration for a GitHub App. For more information about configuring a webhook for your app, see "[Creating a GitHub App](/developers/apps/creating-a-github-app)."  You must use a [JWT](https://docs.github.com/apps/building-github-apps/authenticating-with-github-apps/#authenticating-as-a-github-app) to access this endpoint.
* _GET /orgs/{org}/hooks/{hook_id}/config_ 
  *resource*: orgsget_webhook_config_for_org  
  *description*: Returns the webhook configuration for an organization. To get more information about the webhook, including the `active` state and `events`, use "[Get an organization webhook ](/rest/orgs/webhooks#get-an-organization-webhook)."  You must be an organization owner to use this endpoint.  OAuth app tokens and personal access tokens (classic) need `admin:org_hook` scope. OAuth apps cannot list, view, or edit webhooks that they did not create and users cannot list, view, or edit webhooks that were created by OAuth apps.
* _GET /repos/{owner}/{repo}/hooks/{hook_id}/config_ 
  *resource*: reposget_webhook_config_for_repo  
  *description*: Returns the webhook configuration for a repository. To get more information about the webhook, including the `active` state and `events`, use "[Get a repository webhook](/rest/webhooks/repos#get-a-repository-webhook)."  OAuth app tokens and personal access tokens (classic) need the `read:repo_hook` or `repo` scope to use this endpoint.
* _GET /repos/{owner}/{repo}/actions/workflows_ 
  *resource*: actionslist_repo_workflows  
  *description*: Lists the workflows in a repository.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}_ 
  *resource*: actionsget_workflow  
  *description*: Gets a specific workflow. You can replace `workflow_id` with the workflow file name. For example, you could use `main.yaml`.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/actions/runs_ 
  *resource*: actionslist_workflow_runs_for_repo  
  *description*: Lists all workflow runs for a repository. You can use parameters to narrow the list of results. For more information about using parameters, see [Parameters](https://docs.github.com/rest/guides/getting-started-with-the-rest-api#parameters).  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.  This API will return up to 1,000 results for each search when using the following parameters: `actor`, `branch`, `check_suite_id`, `created`, `event`, `head_sha`, `status`.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}_ 
  *resource*: actionsget_workflow_run  
  *description*: Gets a specific workflow run.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}_ 
  *resource*: actionsget_workflow_run_attempt  
  *description*: Gets a specific workflow run attempt.  Anyone with read access to the repository can use this endpoint.  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs_ 
  *resource*: actionslist_workflow_runs  
  *description*: List all workflow runs for a workflow. You can replace `workflow_id` with the workflow file name. For example, you could use `main.yaml`. You can use parameters to narrow the list of results. For more information about using parameters, see [Parameters](https://docs.github.com/rest/guides/getting-started-with-the-rest-api#parameters).  Anyone with read access to the repository can use this endpoint  OAuth app tokens and personal access tokens (classic) need the `repo` scope to use this endpoint with a private repository.
* _GET /zen_ 
  *resource*: metaget_zen  
  *description*: Get a random sentence from the Zen of GitHub
* _GET /repos/{owner}/{repo}/zipball/{ref}_ 
  *resource*: reposdownload_zipball_archive  
  *description*: Gets a redirect URL to download a zip archive for a repository. If you omit `:ref`, the repository’s default branch (usually `main`) will be used. Please make sure your HTTP framework is configured to follow redirects or you will need to use the `Location` header to make a second `GET` request.  > [!NOTE] > For private repositories, these links are temporary and expire after five minutes. If the repository is empty, you will receive a 404 when you follow the redirect.
