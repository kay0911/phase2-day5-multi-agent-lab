# Lab Guide: Multi-Agent Research System

## Scenario

Bạn cần xây dựng một research assistant có thể nhận câu hỏi dài, tìm thông tin, phân tích và viết câu trả lời cuối cùng. Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline**: một agent làm toàn bộ.
2. **Multi-agent workflow**: Supervisor điều phối Researcher, Analyst, Writer.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có responsibility riêng.
- Shared state phải đủ rõ để debug.
- Phải có trace hoặc log cho từng bước.
- Phải benchmark, không chỉ nhìn output bằng cảm tính.

## Milestone 1: Baseline

File gợi ý:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

TODO(student): thay baseline placeholder bằng một call LLM thật.

## Milestone 2: Supervisor

File gợi ý:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

TODO(student): implement routing policy.

Gợi ý câu hỏi thiết kế:

- Khi nào gọi Researcher?
- Khi nào gọi Analyst?
- Khi nào gọi Writer?
- Khi nào stop?
- Nếu agent fail thì retry hay fallback?

## Milestone 3: Worker agents

File gợi ý:

- `agents/researcher.py`
- `agents/analyst.py`
- `agents/writer.py`

TODO(student): implement từng worker.

## Milestone 4: Trace và benchmark

File gợi ý:

- `observability/tracing.py`
- `evaluation/benchmark.py`
- `evaluation/report.py`

Benchmark tối thiểu:

| Metric | Cách đo gợi ý |
|---|---|
| Latency | wall-clock time |
| Cost | token usage hoặc provider usage |
| Quality | rubric 0-10 do peer review |
| Citation coverage | số claims có source / tổng claims chính |
| Failure rate | số query fail / tổng query |

## Exit ticket

Mỗi nhóm trả lời 2 câu:

1. Case nào nên dùng multi-agent? Vì sao?
   - **Trả lời**: Nên dùng multi-agent cho các tác vụ phức tạp, cần chia nhỏ quy trình (ví dụ: nghiên cứu và tổng hợp bài viết chuyên sâu). Vì việc phân chia vai trò rõ ràng giúp giảm thiểu context window của từng LLM prompt, tối ưu hóa độ chính xác và cho phép kiểm thử, kiểm tra chéo (critic/evaluator) giữa các bước để nâng cao chất lượng đầu ra.
2. Case nào không nên dùng multi-agent? Vì sao?
   - **Trả lời**: Không nên dùng multi-agent cho các tác vụ đơn giản, yêu cầu độ trễ thấp (low latency) và chi phí tối thiểu (ví dụ: chatbot hỏi đáp thông thường, dịch thuật nhanh). Vì kiến trúc multi-agent tăng đáng kể latency (qua nhiều vòng gọi LLM) và nhân số lượng API calls (tăng chi phí USD).

