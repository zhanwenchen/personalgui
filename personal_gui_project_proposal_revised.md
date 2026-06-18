# PersonalGUI: Benchmarking Personal Ecosystem Orchestration in GUI Agents

# Important Links

* [GitHub repo](https://github.com/zhanwenchen/personalgui)
* [Weekly Slides](https://docs.google.com/presentation/d/1SGNyj2Gx3cQeLQHKG3PC3IoljVz0NblvA1JMVGOoYC4/edit?usp=sharing)

What can't CRAB do/measure or represent?

- Authentication.

TODOs:

- A list of types of tasks covered by CRAB vs mine. Make sure the overlap is minimal.
- To claim this is mine, we need to build the fundamental environment that runs successfully.
- Variables
  - User preferences/constraints (text, how to represent? Trees/forest-schema. Easier for optimization and pruning.)
- Metrics
  - **Boundary adherence** measures whether the agent respected work/personal separation, user-preferred channels, and forbidden routes.
  - **Source-of-truth accuracy** measures whether the agent chose the authoritative state when information was duplicated or stale.
  - **Clarification and safety** measure whether the agent asked for help when ambiguity mattered and avoided wrong-recipient, wrong-account, or premature irreversible mock actions. Needs discussions.
  - Level 1 > Level 2 > Level 3:
    - Level 1: **Global success** measures whether the final user-level state matches the target state. This is the headline metric.
    - **Routing accuracy** measures whether each subtask was assigned to a valid or preferred environment.
    - **Handoff correctness** measures whether required values, files, links, dates, codes, or document states were transferred without corruption.
    - **Minimal-transfer behavior** measures whether the agent moved only task-relevant information across environments? This may be more challenging and interesting in its own wright - can be researched separately. SAT? Information bottleneck? For this benchmark paper, can be easy - rules - what can be transferred vs not. Future work can investigate this problem in a Information Theoretical framework.
- What labels can be evaluated automatically?
  - Global success - 
  - Routing accuracy - 
  - Optimality of routing - 
- Baseline not clear - (need a table of ablations)
  - No routing vs simple routing vs Oracle routing
  - Hand off everything vs oracle handoff
  - Loop - .
  - There can be more.
- Contribution: findings. Limitations. What works when?
- Compute proposal submission. terencetcwang.

# Project Description

**TL; DR:** PersonalGUI is a benchmark for evaluating how computer-using agents can complete user requests when the relevant information and applications are distributed across the user's devices.

**Current priority:** The first paper should be a benchmark paper. A privacy-aware agent and a survey are possible follow-ups.

**What I most want feedback on:**

1. Is the same-user / persistent-ecosystem framing sufficiently different from CRAB?
2. Is the v0 scope below narrow enough to start building?
3. Which baseline should be prioritized after the naive-router and oracle-router diagnostics?

## Motivation

Computer-using agent (CUA) benchmarks have made rapid progress on desktop control, mobile control, web navigation, cross-app workflows, and cross-environment execution. The next step is evaluating agents on personal-computing tasks where one user makes one request, but the information and apps needed to complete it live across multiple devices. A request like “submit my taxi expense” may require a receipt on the phone, a portal on the desktop, policy context in the browser, and a notification in chat.

The scientific question is whether a CUA can solve a high-level user request by decomposing it and solving its subgoals through the user’s computing ecosystem. The agent must decide 1) which device environment should handle each subtask, 2) what information needs to move between environments, 3) which app, file, message, or record should be trusted when different places contain overlapping or conflicting information, and 4) when it should ask for clarification before taking an irreversible action.

PersonalGUI builds on existing cross-environment CUA evaluation, especially CRAB, but shifts the focus from “can the agent operate across Ubuntu and Android?” to “can the agent complete a request when the user's state, preferences, permissions, and constraints are distributed across environments?” The intended differentiation is not only that there are multiple environments. It is that the route itself is part of the task.

![image-20260508234152966](/Users/zhanwenchen/Library/Application Support/typora-user-images/image-20260508234152966.png)

## Definitions

A **user** may own device environments **E**, with each **e** containing apps and data such contacts, files, calendars, chats, documents, and constraints (preferences, account boundaries (work/personal)). An agent **f** must divide the task **r** into subgoals **G** (expressed as a graph). The agent must then generate routes **r** that map subtasks **S** to the appropriate apps given by **E**. For example, in an expense task, the route might be: find receipt on phone, read policy in browser, submit form on desktop portal, then notify manager in work chat. In addition to routes, the agent must also pass the correct **handoff artifacts** - information that must move across environments, such as a one-time-password (OTP) code, confirmation code, receipt image, date, link, document title, project milestone, or selected file.

There are unique requirements associated with routing subgoals to environments. **Minimal transfer** is a desirable scenario where only the information needed for the task is transferred (i.e., handed off) between environments. For example, the agent may need to copy a receipt amount, but not expose unrelated personal messages visible near the receipt. A **source-of-truth conflict** occurs when the same apparent fact appears in multiple places but only one source should be treated as authoritative. For example, a project board may supersede an old calendar note.

For example, E

```yaml
environment_set_id: personalgui_v0_desktop_phone
description: >
  Two-environment PersonalGUI setup with a Windows desktop/browser and an Android phone. 
  This file defines the runnable environments,
  available apps, action spaces, and allowed handoff channels.

environments:
  - id: windows_desktop
    display_name: Windows Desktop
    kind: desktop
    platform: windows_11
    access_mode: gui
    launcher:
      type: vm_snapshot
      snapshot_id: windows_desktop_v0
    observation:
      type: screenshot
      resolution: [1920, 1080]
    action_space:
      - click
      - type
      - scroll
      - key_press
      - open_app
      - switch_app
      - upload_file
      - download_file
      - declare_done
      - ask_clarification
    apps:
      - id: desktop_browser
        display_name: Desktop Browser
        kind: browser
        launch_method: pinned_shortcut
        capabilities:
          - open_web_app
          - submit_form
          - upload_file
          - download_file

      - id: expense_portal
        display_name: Mock Expense Portal
        kind: web_app
        launch_method: browser_url
        parent_app: desktop_browser
        url: http://mock.local/expense
        account_boundary: work
        capabilities:
          - create_expense_report
          - attach_receipt
          - submit_expense

      - id: work_chat
        display_name: Mock Work Chat
        kind: chat_app
        launch_method: browser_url
        parent_app: desktop_browser
        url: http://mock.local/work-chat
        account_boundary: work
        capabilities:
          - read_channel
          - search_contacts
          - send_message
          - attach_file

      - id: document_editor
        display_name: Mock Document Editor
        kind: document_app
        launch_method: browser_url
        parent_app: desktop_browser
        url: http://mock.local/docs
        account_boundary: work
        capabilities:
          - open_document
          - edit_document
          - save_document
          - share_link

  - id: android_phone
    display_name: Android Phone
    kind: mobile
    platform: android_emulator
    access_mode: gui
    launcher:
      type: emulator_snapshot
      snapshot_id: android_phone_v0
    observation:
      type: screenshot
      resolution: [1080, 2400]
    action_space:
      - tap
      - type
      - scroll
      - long_press
      - open_app
      - switch_app
      - copy_value
      - share_file
      - declare_done
      - ask_clarification
    apps:
      - id: phone_photos
        display_name: Phone Photos
        kind: media_app
        account_boundary: personal
        capabilities:
          - view_image
          - share_image
          - read_visible_text

      - id: mock_authenticator
        display_name: Mock Authenticator
        kind: authenticator_app
        account_boundary: personal
        capabilities:
          - view_one_time_code

      - id: personal_calendar
        display_name: Personal Calendar
        kind: calendar_app
        account_boundary: personal
        capabilities:
          - view_event
          - create_event
          - edit_event

      - id: phone_chat
        display_name: Phone Chat
        kind: chat_app
        account_boundary: personal
        capabilities:
          - read_message
          - search_contacts
          - send_message
          - share_file

handoff_channels:
  - id: phone_to_desktop_file_bridge
    from_environment: android_phone
    to_environment: windows_desktop
    mechanism: controlled_file_transfer
    artifact_types:
      - image_file
      - document_file
      - link

  - id: phone_to_desktop_clipboard
    from_environment: android_phone
    to_environment: windows_desktop
    mechanism: controlled_clipboard
    artifact_types:
      - text_value
      - code
      - date
      - amount

  - id: desktop_to_phone_clipboard
    from_environment: windows_desktop
    to_environment: android_phone
    mechanism: controlled_clipboard
    artifact_types:
      - text_value
      - link
      - confirmation_code

agent_visible_setup:
  environment_names:
    - windows_desktop
    - android_phone
  app_names:
    - desktop_browser
    - expense_portal
    - work_chat
    - document_editor
    - phone_photos
    - mock_authenticator
    - personal_calendar
    - phone_chat
```



## Goal and Task Formalism

The goal is to build a benchmark, harness, metrics, and baseline suite for evaluating whether GUI agents can complete one user request when the relevant information and actions are spread across that user's apps and devices. The core task unit is

$$
\tau = (u, E, x_0, r, G, y^*)
$$

where \(u\) is a synthetic user, \(E\) is the user's set of apps/devices/environments, \(x_0\) is the initial contents of those apps/devices plus the user's constraints and preferences, \(r\) is one natural-language request, \(G\) is a latent task graph, and \(y^*\) is the desired global end state. The agent receives only the user request and graphical user interface (GUI) access. The evaluator has privileged backend access only for resetting tasks, checking final state, and computing diagnostic metrics.

The latent task graph \(G\) specifies the subtasks needed to complete the request, their dependencies, which environments are required/preferred/flexible/forbidden for each subtask, what information or artifacts must move between environments, and which app, file, message, or record should be trusted when different places contain overlapping or conflicting information. The agent does not observe \(G\). It must infer a valid route from the request and from what it observes while interacting with the GUIs.

An episode unfolds through GUI interaction. At step \(t\), the benchmark has hidden backend contents

$$
x_t = \{x_t^{(e)} : e \in E\},
$$

where \(x_t^{(e)}\) is the current content of environment \(e\), such as files, messages, calendar events, documents, mock receipts, project-board items, app records, or user-preference settings. The agent does not directly observe \(x_t\). Instead, it observes the rendered interface of the current environment:

$$
o_t = O(e_t, x_t^{(e_t)}).
$$

The agent then chooses an action:

$$
a_t = (e_t, \alpha_t),
$$

where \(e_t \in E\) is the app/device/environment being acted in, and \(\alpha_t \in \mathcal{A}_{e_t}(o_t)\) is an environment-specific action. Examples include clicking, typing, opening an app, editing a document, reading a message, switching environments, copying a value, attaching a file, sending a notification, asking the user for clarification, or transferring a needed artifact from one environment to another.

The benchmark updates the app/device contents through a transition function:

$$
x_{t+1} = T(x_t, a_t).
$$

This transition may affect one environment or multiple environments. For example, editing a document changes the document state; submitting a receipt changes the mock expense-portal state; sending a chat message changes the chat state; and transferring a code, file, link, or value creates a handoff between environments.

A route is the sequence of environments and handoffs used to complete the request:

$$
\rho = (e_1, e_2, \ldots, e_T; h_1, h_2, \ldots),
$$

where each \(h_i\) is a handoff artifact such as a value, file, image, link, code, document edit, or summarized piece of context transferred from one environment to another. PersonalGUI evaluates not only whether the final task is completed, but whether the route is appropriate for the synthetic user.

The benchmark should evaluate how well the agent decomposes the request, chooses the correct app/device for each subtask (routing), transfer required information without corruption, respect user-specific constraints, avoid unnecessary transfer of sensitive information, use the current or official version of the user's information, ask for clarification when ambiguity matters, and produce the desired global state.

Formally, the evaluator checks the final backend contents against the desired global end state and task graph:

$$
\operatorname{Eval}(x_T, y^*, G)
\rightarrow
\{
\text{success},
\text{routing accuracy},
\text{handoff correctness},
\text{minimal-transfer behavior},
\text{boundary/preference adherence},
\text{trusted-source selection},
\text{clarification quality}
\}.
$$

This setup separates several failure modes that ordinary task success can hide. An agent may understand the request but choose the wrong app, choose the right app but take the wrong GUI action, transfer the wrong value between devices, use an outdated record instead of the current one, mix work and personal channels, reveal more information than necessary, or act without clarification when two recipients or accounts are ambiguous.

## v0 Scope

The v0 benchmark should be deliberately small. The goal is to validate the formalism and pipeline before scaling.

**v0 includes:**

* 2 synthetic users
  * 3 environments: Android Phone, Windows, MacBook

* 3 mock app families: calendar/chat, mock authenticator, and document/planner.
* 10–20 curated task instances.
* Deterministic reset and grading.
* Functional verifiers for each task.
* Human baseline and one agent baseline if runnable.

The v0 success condition is showing that route choice, handoff, and user-specific constraints can be made executable and measurable in a small benchmark.

## Data Collection Pipeline

The first stage of the project is to collect realistic workflow, routes, handoffs, ambiguities, and user constraints. We 1) start with lab-authored example tasks so engineering is not blocked on crowdsourcing, 2) crowdsource abstract task sketches, route choices, handoff requirements, ambiguity judgments, and realism ratings from Prolific, and 3) convert selected sketches into synthetic executable benchmark tasks.

Prolific can then be used for realistic task elicitation, task decomposition ground truths, and validation. For example, a participant may say that an expense task often involves finding a receipt on the phone, submitting a form through a desktop portal, and notifying a manager in work chat.

Crowdsourced judgments can capture three things: how people would break down the task, which apps/devices they would use for each step, and what information needs to move between apps/devices. They can also flag ambiguity, such as when the agent should ask for clarification, and rate whether the task feels realistic. These human-derived judgments help define routes, handoffs, constraints, and diagnostics for PersonalGUI. They are later converted into synthetic executable benchmark tasks and are not shown to the agent during evaluation.

Selected task sketches are converted into synthetic benchmark instances: fake users, fake contacts, fake calendars, fake chat/email histories, fake receipts, fake documents, fake project boards, sandboxed app backends, route labels, handoff labels, desired final states, and expected backend conditions that functional verifiers can check.

A small Prolific pilot can target roughly 30 participants and produce a few hundred candidate task sketches or route annotations before filtering. The v0 benchmark should still use only 10–20 curated executable tasks. The larger pool is useful for selecting realistic tasks and validating route labels, not for scaling immediately.

## Benchmark Harness and Instrumentation Pipeline

PersonalGUI separates the agent-facing interface from the benchmark harness, i.e. the logic of the benchmark evaluation engine. The agent interacts only through the user request, GUI observations, and user-visible history. The harness is used for reset, environment launch, logging, instrumentation, and grading. The harness maintains information that the agent must not see:

* **Initial app/device contents:** the seeded files, messages, calendars, receipts, documents, mock portals, and app records.
* **Hidden task graph:** the subtasks, dependencies, valid routes, forbidden routes, and required handoffs.
* **Route labels:** which apps/devices/environments are required, preferred, flexible, or invalid for each subtask.
* **Desired final state:** the target outcome used to determine whether the task was completed.
* **Functional verifiers:** deterministic checks for task success and diagnostic metrics.
* **Instrumentation APIs:** internal APIs for resetting tasks, reading backend state, logging actions, detecting handoffs, and computing metrics.

The agent must discover the receipt, route, handoff, and recipient through GUI interaction. The harness uses hidden state only to reset the task, instrument the interaction, and grade the final outcome.

This separation keeps the benchmark fair: agents are evaluated on whether they can infer and execute the correct task, while the harness can still reset tasks deterministically and grade outcomes reliably.

## Using PersonalGUI to Evaluate an Agent

This section describes how an external researcher would use PersonalGUI to evaluate a GUI agent such as Agent S3, OS-Copilot, UI-TARS, OpenCUA, or a new agent system. The researcher wraps their agent in a small adapter. The adapter receives only the user request, available app/device names, GUI observations, and user-visible history.

```python
agent.setup(task_id, request, environments)
agent.act(observation, history) -> action
```

The agent does not receive backend app state, hidden task graphs, route labels, desired final states, verifier outputs, or grading APIs.

```python
def evaluate_task(task, agent, max_steps):
    envs, logger, hidden, agent_visible = prepare_task(task)

    agent.setup(
        task_id=agent_visible["task_id"],
        request=agent_visible["request"],
        environments=agent_visible["environments"],
    )

    observation = envs.observe()
    history = []

    for step in range(max_steps):
        action = agent.act(observation, history)
        event = envs.step(action)

        logger.record(step, observation, action, event)
        history.append((observation, action, event))

        observation = envs.observe()

        if action.type == "declare_done" or task_is_done(task, envs):
            break

    final_state = read_backend_state(envs)
    metrics = run_verifiers(task, final_state, logger)

    return metrics, logger.export()
```

PersonalGUI reports global task success plus diagnostic metrics: routing accuracy, handoff correctness, minimal-transfer behavior, boundary/preference adherence, trusted-source selection, clarification behavior, and irreversible-action/safety violations.

A full benchmark run applies the same loop to every task-agent pair:

```python
def evaluate_split(tasks, agents, max_steps):
    results = {}

    for agent_name, agent in agents.items():
        results[agent_name] = []

        for task in tasks:
            metrics, log = evaluate_task(task, agent, max_steps)
            results[agent_name].append((task.task_id, metrics, log))

    return aggregate_results(results)
```

This keeps the evaluation protocol simple: choose a PersonalGUI split, plug in an agent adapter, run the harness, and compare agents using the same verifier-based metrics.

## Initial Task Families

The first task families should be chosen because they isolate routing and handoff, with the following initial examples:

* **Mock authenticator handoff:** a desktop app requires a sandboxed four-digit code visible only on the phone.
* **Expense submission:** the receipt is on the phone, but the reimbursement portal is desktop-only.
* **Daily planning:** the agent must combine personal calendar, work calendar, and planner state without mixing boundaries.
* **Document editing with external context:** the paper draft is in the browser, but a relevant note or reviewer comment is in phone/chat.
* **Source-of-truth resolution:** duplicated information appears in two places, but one source is marked as newer or authoritative.

## Metrics

The benchmark should report global success and fine-grained diagnostic metrics:

- **Global success** measures whether the final user-level state matches the target state. This is the headline metric.
- **Routing accuracy** measures whether each subtask was assigned to a valid or preferred environment.
- **Handoff correctness** measures whether required values, files, links, dates, codes, or document states were transferred without corruption.
- **Minimal-transfer behavior** measures whether the agent moved only task-relevant information across environments.
- **Boundary adherence** measures whether the agent respected work/personal separation, user-preferred channels, and forbidden routes.
- **Source-of-truth accuracy** measures whether the agent chose the authoritative state when information was duplicated or stale.
- **Clarification and safety** measure whether the agent asked for help when ambiguity mattered and avoided wrong-recipient, wrong-account, or premature irreversible mock actions.

## Related Works

The closest benchmark competitor is CRAB, which already studies cross-environment GUI agents over Ubuntu and Android. Our proposed distinction is that PersonalGUI treats the user ecosystem as the unit of evaluation. A task is not just “operate across two environments.” A task in our benchmark is “complete a one user whose relevant apps and data are distributed across environments.” This makes user identity, route choice, handoff, work/personal boundaries, source-of-truth reasoning, recipient ambiguity, and minimal-transfer constraints part of the evaluation.

Other relevant benchmarks include OSWorld, AndroidWorld, MobileWorld, Windows Agent Arena / WindowsWorld, and ScreenSuite. They are useful scale, environment, and GUI-control references.

## Publishable Findings

It should establish that personal ecosystem orchestration is measurable and that current agents have systematic failures on this axis. Examples plausible publishable findings could be:

1. Current GUI agents degrade when one user request requires cross-environment decomposition, routing, and handoff.
2. Oracle-routing and oracle-handoff produce large gains, showing that environment selection and state transfer are separable bottlenecks.
3. Minimal-transfer and work/personal boundary constraints reveal failures that ordinary task success would miss.
4. Source-of-truth and recipient-disambiguation tasks expose user-ecosystem errors not captured by generic GUI benchmarks.

A follow-up method paper can address any such bottlenecks found by the benchmark paper.

## Project Plan

**Phase 0: Benchmark familiarization.** Reproduce or closely inspect CRAB or OSWorld. Summarize how tasks, resets, environments, baselines, and evaluators are implemented. Identify exactly what is missing for same-user multi-environment orchestration.

**Phase 1: v0 specification.** Define the synthetic user schema, environment schema, task graph schema, route labels, handoff artifacts, privacy/minimal-transfer labels, boundary labels, source-of-truth labels, recipient ambiguity labels, and functional verifier contracts.

**Phase 2: Minimal harness.** Build example synthetic users, environments, mock apps, initial tasks, deterministic reset, logging, and functional evaluation. The first engineering target is five tasks that can be run repeatedly and graded deterministically.

**Phase 3: Pilot evaluation.** Expand to 10–20 tasks and run human, naive-router, planner-executor, oracle-router, oracle-handoff, one frontier agent, and 3-5 baseline agents. Analyze failures by decomposition error, routing error, GUI grounding error, handoff error, missing clarification, boundary violation, source-of-truth error, recipient error, and evaluator error.

**Phase 4: Crowdsourcing and validation.** Run a small Prolific pilot for workflow sketches, route annotations, minimal-transfer judgments, ambiguity labels, and realism checks. Use the results to revise task families and labels.

**Phase 5: Scale dataset.** Expand to 400 task instances only after the schema, harness, Prolific protocol, and evaluators are stable. Add more users, task families, environments, ambiguity cases, fallback cases, and privacy/boundary cases incrementally.

## Relevant Reading

**Highest priority:**

* CRAB: https://arxiv.org/abs/2407.01511 and https://github.com/camel-ai/crab
* OSWorld: https://os-world.github.io/ and https://github.com/xlang-ai/OSWorld
* AndroidWorld: https://google-research.github.io/android_world/
* MobileWorld: https://github.com/Tongyi-MAI/MobileWorld
* ScreenSuite: https://github.com/huggingface/screensuite

**Later reading / baselines:**

* Windows Agent Arena / WindowsWorld: https://microsoft.github.io/WindowsAgentArena/
* UI-TARS: https://github.com/bytedance/UI-TARS
* OpenCUA: https://opencua.xlang.ai/
* Agent S / Agent S3: https://github.com/simular-ai/Agent-S
* Prolific: https://www.prolific.com/academic-researchers
* Apple Continuity / iPhone Mirroring as product motivation, not a benchmark competitor: https://www.apple.com/macos/continuity/ and https://support.apple.com/en-us/120421

## Milestones

* Reproduce or closely inspect one existing benchmark setup, preferably CRAB or OSWorld.
* Write the v0 task schema and metric definitions.
* Implement one synthetic user, two environments, and three mock app families.
* Build five deterministic pilot tasks and functional verifiers.
* Run the first small baseline table on five tasks.
* Expand to 10–20 pilot tasks after the first five are stable.
* Run the Prolific pilot.
* Decide whether to scale to 400 tasks based on pilot stability and diagnostic value.

## Helpful Technology

* pyautogui is a mouse/keyboard interface for controling the computer screen (GUI).
* Use Docker/VM snapshots for reproducible desktop/browser state where possible.
* Use Android emulator + ADB, or reuse an existing Android benchmark environment.
* Use deterministic mock backends and functional verifiers rather than live services.

# Big-Picture Outcomes

For Zhanwen:

* Experience building a benchmark, harness, and controlled evaluation suite for GUI agents.
* Deeper expertise in GUI agents, personal-assistant workflows, and evaluation methodology.

For the lab:

* Reusable infrastructure for work on trustworthy personal AI assistants, privacy-aware orchestration, and reliable GUI automation.

For us both:

* A scientific publication introducing the benchmark, baselines, and failure analysis.
* A possible follow-up paper on route-aware, handoff-aware, source-of-truth-aware, or privacy-aware GUI agents.

# Communications

## Weekly Slide Deck

Please make weekly slides covering:

1. Agenda
2. Main objective
3. Main updates and sticking points
   1. What was done from last week's TODOs?
   2. What needs feedback?
   3. What is blocked?
4. Next steps
   1. What experiment, reading, implementation, or writing milestone is next?
