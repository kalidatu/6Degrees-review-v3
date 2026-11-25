# 6Degrees V3 · Stage 6C

## Run on Windows with Python 3.12

Extract the entire ZIP to a fresh folder. Open the extracted **6Degrees-V3** folder and double-click **Start-6Degrees.bat**. It locates the app relative to the launcher, creates or reuses a local Python 3.12 virtual environment, installs the pinned requirements and starts Streamlit on loopback. Install Python 3.12 for Windows first, with the Python launcher or a Python 3.12 executable on PATH. The first dependency installation needs internet access. Leave the console open while reviewing. To run manually, open PowerShell in the same folder and use the following commands.

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r stage5/requirements.txt
.\.venv\Scripts\python.exe -m streamlit run stage5_app.py --server.address 127.0.0.1
~~~

Open http://127.0.0.1:8501 or the local address printed in PowerShell. Press Ctrl+C to stop. The explorer uses bundled vis-network assets and a fictional in-memory network. The separate v0.6 application starts from app.py.

## Check the V3 layout

With the local app running and Playwright installed as described under **Repeat the tests**, run this command in a second PowerShell window from the project folder:

~~~powershell
.\.venv\Scripts\python.exe -m stage5.layout_check --screenshots review-local
~~~

The geometry checks use 1366 × 768 and 1920 × 1080 at default zoom. The remaining sections describe the inherited explorer features and their regression checks.

## Stage 6B stress fixtures

See the [Manual Testing Guide](../MANUAL-TESTING-GUIDE.md) for the four exact names, IDs, expected counts and sample contacts. Search 901 (Nina, 9), 902 (Felix, 15), 903 (Alex, 126) or 904 (Taylor, 1,000). Each personal list now uses the heading **Member’s Network (total)**. Direct connections remains the profile statistic.

The named review members and their deterministic, explicit edges are defined in `stage5/stress_fixture.py`. Every new contact belongs only to its own fictional hub. Set `SIXDEGREES_REVIEW_FIXTURES=0` before starting the local app to exclude these four networks. The supplied tests expect the default enabled setting and default graph budgets. The named browser suite exercises all four sizes and runs the Mary → Cleo → Kevin walk separately through the graph and the Network panel.

## Stage 6B changelog and local review

- The separate Connections panel below the profile searches every permitted direct contact by partial name or exact ID. The panel uses 25 rows per page. Up to 15 matching contacts take their natural height. Larger result sets use a scrolling region capped at 300 pixels. The profile previews up to ten chips.
- **All** and **Direct** both show all permitted one-edge relationships. **Mutual** intersects the selected member’s contacts with David’s. **Route Relevant** intersects them with members on the currently displayed 3 or 5 paths. Explore Mode has no searched destination, and a disconnected destination has no matching route members.
- Panel selections, profile chips and graph nodes use the same navigation handler. Back and Forward restore the graph viewport, trail, mode, route limit, profile and search controls, including the panel’s selected row, query, filter, page and scroll. Opening a new member after Back discards the forward branch. Home clears both finders and both history directions.
- Default graph budgets are 16 total nodes and 32 undirected edges. Route members are included first with every permitted edge between them, even if this exceeds a budget. Remaining contacts are considered in member-ID order and included only when all their visible edges fit. To override, set the positive integer PowerShell environment variables `$env:SIXDEGREES_NODE_BUDGET` and `$env:SIXDEGREES_EDGE_BUDGET` before launching. Run the supplied acceptance tests with the defaults.
- The Stage 6A rollback point is local tag `stage6a-rollback` at commit `dc20d90`. The approved Stage 6A archive remains a standalone rollback build.

**Try Sinbad.** Enter `Sinbad` in People Finder. In Sinbad’s Network, try Mutual (Laura), Route Relevant, and then All. Type `Niko` in the panel and click the row. Back restores Sinbad, the local query and the map. Home returns to David.

**Try the stress fixtures.** Enter hub ID `2000` (100 contacts) or `2001` (1,000). Both belong to an isolated fictional test component. Its two hubs share 100 members, with cross-connections between consecutive shared contacts. On #2001, switch pages, scroll, or search for `#4000` and open the result. The graph initially omits that contact. The header and profile always show the full degree. All test members have names beginning with “Test”.

**Performance scope.** Budgets limit optional graph drawing and pagination limits the panel DOM. The prototype still sends the selected member’s permitted contact summaries to the browser and filters them there. Global People Finder, graph loading and pathfinding use the in-memory demo. Highly connected route members alone can exceed the edge budget. Before moving to production-scale data, measure representative hubs and concurrent searches, move contact filtering and paging to a permission-aware indexed service, and reuse permission-scoped graph indexes for path queries.

## Review the member profile

Start on David and click Mary’s chip in the card. Verify Mary has 9 contacts and is one degree from David. Press Back. Search for Sinbad, choose five routes, and click Gio’s chip. Back restores Sinbad’s profile and the five-route map. Search for IDs 101 and 102 to compare the two John Smith profiles and explore their contacts.

The circular monogram is the default for all bundled demo profiles. An optional public HTTPS photo URL can replace it. Missing images and failed loads show the monogram. Public biographies are limited to 200 displayed characters. The chip list scrolls when it outgrows the compact card.

### Changed files

- `stage5_app.py` supplies the card with the focused member’s public fields, shortest distance and permitted contacts. Both graph and chip events use the same navigation and replay checks.
- `stage5/directory.py` adds optional public photo and biography fields and four fictional biographies.
- `stage5/profile/index.html` and `profile.js` implement the card, avatar fallback, statistics and member-ID chips.
- `stage5/profile_check.py` tests profiles, photos, chip navigation and restored state.
- `stage5/browser_check.py` and `stage5/search_check.py` check the redesigned card throughout the existing graph and finder regression suites.
- `stage5/README.md` contains the Windows setup and review steps.

## Review People Finder

1. Type `Sin` to see Sinbad, then press Enter to open his map. Enter opens the sole match after applying the state filter. Multiple matches remain available for explicit selection. Names can match anywhere, including `Taylor Thousand`.
2. Type `John Smith`. Click the Long Beach result, then the Tacoma result. Each radio selection immediately opens the corresponding map. Filtering to Washington narrows the list without navigating.
3. From either John’s map, search for Sinbad and set **Maximum routes** to 5. Click Gio, then Mary. The finder clears when exploration begins. Press Back to return to Gio, Back again for Sinbad’s five-route map, and Back again for John’s original search.
4. Press Home to clear the controls and return to David.

The original 25 members retain their IDs and 41 relationships with one another. John Smith #101 connects to Alba, Paz and Tala. His shortest route from David runs through Mary and Alba. John Smith #102 connects to Nell Vale, Ada Finch and Tess Reed. Nell and Ada also know each other. This four-person network is independent of David’s. An isolated opt-out fixture exercises exclusion. Results and filters use only the demo’s public profile fields. State is the first optional filter. Name matching ignores case and surrounding whitespace and supports substrings. Typo correction, aliases, live directory access and authentication are outside this build.

## Review the expanded network

* Walk David → Mary → Kevin → Laura → Sinbad. The profile counts are 2, 9, 9, 7 and 6. Sinbad is two degrees from David. Laura is their only mutual contact.
* From Home, try David → Mary → Gio → Sinbad. Gio belongs to Mary's, Kevin's and Sinbad's networks. Each displayed edge is explicitly declared in stage5/demo.py.
* Explore the outer cycle via David → Mary → Bram → Paz → Sol → Tala, or David → Laura → Sinbad → Niko → Rhea → Tala.
* Drag empty space to pan and use the mouse wheel to zoom. Back restores the preceding neighborhood and its camera. Home resets the active trail and framing. The click counter is cumulative.
* The visible graph combines direct contacts with the manual and shortest routes. A click on a route reference outside the current person's direct contacts starts a new manual segment. The navigation trail records the jump and Back restores the previous segment.
* Longer routes can extend beyond the initial frame. Pan or zoom out to inspect them. Edge crossings remain possible in dense neighborhoods.

## Repeat the tests

From the repository root, run the unit tests:

~~~powershell
.\.venv\Scripts\python.exe -m unittest stage5.test_demo -v
~~~

With the app running, open a second PowerShell window in the same folder and run:

~~~powershell
.\.venv\Scripts\python.exe -m pip install playwright
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m stage5.browser_check --screenshots screenshots
~~~

Use --url to select a different local server, --width and --height for desktop sizes, or --chromium for an installed browser binary. The browser check uses a fresh session. Review screenshots and test results are under review/ in the ZIP.

## Connection Map review

Submit Sinbad (ID 5) and compare **Maximum routes** at 3 and 5. The numbered list is ordered by hop count. David is marked as the origin and Sinbad as the destination. The map contains the union of the listed routes, Sinbad’s immediate contacts, and every permitted edge among those members.

Thin solid edges show ordinary relationships. Bold solid edges show secondary routes on the map and the manual trail in Explore Mode. Dashed blue always takes priority for edges on the first-ranked shortest route, including shared segments. When routes tie on length, the NetworkX 3.4.2 unweighted Yen generator uses the same graph built in sorted member-ID order on every run. A lazy 3- or 5-result limit avoids generating every simple route.

Click any person on the map, including the destination, to switch to Explore Mode. Back restores the prior view, finder selection, and map limit. Home clears the query, state filter and result selection. Select John Smith #102 to see “No known connection to David.” For very dense graphs the route-count limit bounds the number of displayed routes, while the destination can still have many direct contacts and cross-edges. Pan or zoom to inspect individual segments.
