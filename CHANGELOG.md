# 更新记录

## Unreleased

- `0001_init` 改为显式 `op.create_table` / `op.create_index`，运行期走 `alembic upgrade`
- `app/` 只依赖 `ports`，新增内存假实现用例
- 开 ruff `E2`/`E3`；CI 增加 `docker build` 与 `/health` 探活

## 1.0.0

- 支柱占比核算
- 30 天复用窗口
- 未来 7 天日历缺口
- 模型选题与未验证标记
- 库存选题自动排期
