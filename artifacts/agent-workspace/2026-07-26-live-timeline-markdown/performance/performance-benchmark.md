# Agent Timeline Markdown Performance Evidence

- Status: `PASS`
- Source commit: `3dcf465cf5650af206d3b0c8ec6665f4bdd68266`
- Captured at: `2026-07-26T20:19:04+08:00`

## Measurements

| Path | Measurement |
| --- | --- |
| 10,000-row model | `{'rows': 10000, 'elapsed_ms': 0.035, 'permanent_index_widgets_sampled': 0}` |
| 1,000 Markdown rows | `{'rows': 1000, 'elapsed_ms': 323.316}` |
| 1,000 streaming deltas | `{'events': 1000, 'elapsed_ms': 31.676, 'projected_rows': 1, 'body_characters': 1000, 'ui_throttle_interval_ms': 50}` |
| 500 lifecycle events | `{'events': 500, 'elapsed_ms': 53.939, 'projected_rows': 1, 'detail_count': 250}` |
| Viewport resize | `[{'width_px': 1400, 'height_px': 200, 'elapsed_ms': 14.738}, {'width_px': 984, 'height_px': 242, 'elapsed_ms': 1.793}, {'width_px': 1400, 'height_px': 200, 'elapsed_ms': 0.28}]` |
| 150% font | `{'height_px': 474, 'elapsed_ms': 25.079}` |
| 50 KiB reply | `{'source_bytes': 51198, 'elapsed_ms': 55.351, 'height_px': 23863.0, 'document_width_px': 984.0}` |
| Nested list/table/code | `{'elapsed_ms': 3.921, 'height_px': 317.0, 'document_width_px': 984.0}` |
| Memory | `{'python_current_mib': 4.759, 'python_peak_mib': 4.943, 'rss_before_kib': 53524, 'rss_after_kib': 99980, 'rss_growth_mib': 45.367}` |
| Cache | `{'entries': 256, 'maximum_entries': 256, 'hits': 1, 'misses': 1002, 'hit_rate': 0.000997}` |
| Maximum measured GUI-thread stall | `55.351 ms` |

## Threshold checks

- [x] `model_10000`
- [x] `markdown_1000`
- [x] `streaming_1000`
- [x] `lifecycle_500`
- [x] `resize`
- [x] `width_bounded`
- [x] `long_50kb`
- [x] `maximum_gui_stall`
- [x] `memory`
- [x] `cache_bounded`

The benchmark exercises native Qt model/view and QTextDocument paths offscreen. Target-host compositor and assistive-technology field performance remain separate validation layers.
