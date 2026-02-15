from pathlib import Path

path = Path(r"G:\proj\Decky-send\friendeck\lib\main.dart")
text = path.read_text(encoding="utf-8")

old_top = """                                const SizedBox(height: 10),
                                SingleChildScrollView(
                                  scrollDirection: Axis.horizontal,
                                  child: Row(
                                    children: _segments(_path)
                                        .map(
                                          (segment) => Padding(
                                            padding: const EdgeInsets.only(
                                              right: 6,
                                            ),
                                            child: FilterChip(
                                              label: Text(segment.label),
                                              selected: segment.path == _path,
                                              onSelected: (_) {
                                                if (segment.path != _path) {
                                                  _load(segment.path);
                                                }
                                              },
                                            ),
                                          ),
                                        )
                                        .toList(),
                                  ),
                                ),
"""
if old_top not in text:
    raise SystemExit("top breadcrumb block not found")
text = text.replace(old_top, "                                const SizedBox(height: 8),\n", 1)

anchor = """                  const SizedBox(height: 10),
                  Expanded(
                    child: Padding(
                      padding: EdgeInsets.symmetric(horizontal: horizontal),
                      child: RefreshIndicator(
                        onRefresh: () => _load(_path),
                        child: _buildList(),
                      ),
                    ),
                  ),
                  AnimatedSwitcher(
"""
insert = """                  const SizedBox(height: 10),
                  Expanded(
                    child: Padding(
                      padding: EdgeInsets.symmetric(horizontal: horizontal),
                      child: RefreshIndicator(
                        onRefresh: () => _load(_path),
                        child: _buildList(),
                      ),
                    ),
                  ),
                  Builder(
                    builder: (context) {
                      final crumbs = _segments(_path);
                      return Container(
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: scheme.surfaceContainer,
                          borderRadius: const BorderRadius.only(
                            topLeft: Radius.circular(12),
                            topRight: Radius.circular(12),
                          ),
                        ),
                        padding: EdgeInsets.symmetric(
                          horizontal: horizontal,
                          vertical: 2,
                        ),
                        child: SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            children: [
                              for (var i = 0; i < crumbs.length; i++) ...[
                                TextButton(
                                  onPressed:
                                      (_busy || crumbs[i].path == _path)
                                      ? null
                                      : () => _load(crumbs[i].path),
                                  style: TextButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 3,
                                    ),
                                    minimumSize: const Size(0, 32),
                                    tapTargetSize:
                                        MaterialTapTargetSize.shrinkWrap,
                                    foregroundColor: scheme.onSurfaceVariant,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                  ),
                                  child: Text(
                                    crumbs[i].label,
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodySmall
                                        ?.copyWith(
                                          fontWeight: FontWeight.w600,
                                          color: crumbs[i].path == _path
                                              ? scheme.onSurface
                                              : scheme.onSurfaceVariant
                                                    .withValues(alpha: 0.9),
                                        ),
                                  ),
                                ),
                                if (i < crumbs.length - 1)
                                  Padding(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 2,
                                    ),
                                    child: Text(
                                      '/',
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall
                                          ?.copyWith(
                                            color: scheme.onSurfaceVariant
                                                .withValues(alpha: 0.72),
                                          ),
                                    ),
                                  ),
                              ],
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                  AnimatedSwitcher(
"""
if anchor not in text:
    raise SystemExit("bottom anchor not found")
text = text.replace(anchor, insert, 1)

path.write_text(text, encoding="utf-8")
print("patched")
