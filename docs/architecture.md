# Architecture

PentestGPT-NG separates orchestration, model providers, execution, knowledge and evidence.

## Initial flow

1. Load an immutable authorization manifest.
2. Create or restore a session.
3. Ask the Planner for one bounded task.
4. Validate that the task can be performed under the manifest.
5. Send the structured task to an Executor.
6. Persist raw evidence and the normalized result.
7. Update the task state without converting unverified work into a verified result.

## Boundaries

- The core never accepts unrestricted shell commands from a language model.
- LLM providers implement one neutral protocol.
- Tool adapters and sandboxes will be separate packages.
- Knowledge sources are retrieved on demand rather than inserted wholesale into prompts.
- The first release is limited to authorized web, API and source-code laboratories.
