from pathlib import Path

path = Path(r"G:\proj\Decky-send\friendeck\lib\main.dart")
text = path.read_text(encoding="utf-8")

# 1) Root segment label uses slash, not "Root".
text = text.replace(
    "      const _PathSegment(label: 'Root', path: '/'),",
    "      const _PathSegment(label: '/', path: '/'),",
    1,
)

# 2) Remove old top breadcrumb chips block.
old_top = """                            const SizedBox(height: 10),
                            SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                children: _segments(_path)
                                    .map(
                                      (s) => Padding(
                                        padding: const EdgeInsets.only(
                                          right: 6,
                                        ),
                                        child: FilterChip(
                                          label: Text(s.label),
                                          selected: s.path == _path,
                                          onSelected: (_) {
                                            if (s.path != _path) {
                                              _load(s.path);
                                            }
                                          },
                                        ),
                                      ),
                                    )
                                    .toList(),
                              ),
                            ),
                            const SizedBox(height: 8),
"""
new_top = """                            const SizedBox(height: 8),
"""
if old_top not in text:
    raise SystemExit("top breadcrumb block not found")
text = text.replace(old_top, new_top, 1)

# 3) Add bottom breadcrumb bar above bottom navigation and keep selection bar above it.
old_bottom = """                  const SizedBox(height: 10),
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
                    duration: const Duration(milliseconds: 180),
                    child: _selectionMode
                        ? Container(
                            key: const ValueKey('file-selection-bar'),
                            margin: EdgeInsets.fromLTRB(
                              horizontal,
                              0,
                              horizontal,
                              12,
                            ),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 10,
                            ),
                            decoration: BoxDecoration(
                              color: scheme.surfaceContainerHigh,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: scheme.outlineVariant.withValues(
                                  alpha: 0.35,
                                ),
                              ),
                              boxShadow: const [
                                BoxShadow(
                                  color: Color(0x200D365A),
                                  blurRadius: 16,
                                  offset: Offset(0, 6),
                                ),
                              ],
                            ),
                            child: Row(
                              children: [
                                Text('Selected \\${_selected.length}'),
                                const Spacer(),
                                IconButton(
                                  onPressed: _busy ? null : _downloadSelection,
                                  icon: const Icon(Icons.download_rounded),
                                  tooltip: 'Download',
                                ),
                                IconButton(
                                  onPressed: _busy ? null : _deleteSelection,
                                  icon: const Icon(Icons.delete_rounded),
                                  tooltip: 'Delete',
                                ),
                                IconButton(
                                  onPressed: _busy
                                      ? null
                                      : () => setState(_selected.clear),
                                  icon: const Icon(Icons.close_rounded),
                                  tooltip: 'Clear selection',
                                ),
                              ],
                            ),
                          )
                        : const SizedBox.shrink(),
                  ),
"""
new_bottom = """                  const SizedBox(height: 10),
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
                    duration: const Duration(milliseconds: 180),
                    child: _selectionMode
                        ? Container(
                            key: const ValueKey('file-selection-bar'),
                            margin: EdgeInsets.fromLTRB(
                              horizontal,
                              0,
                              horizontal,
                              8,
                            ),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 10,
                            ),
                            decoration: BoxDecoration(
                              color: scheme.surfaceContainerHigh,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: scheme.outlineVariant.withValues(
                                  alpha: 0.35,
                                ),
                              ),
                              boxShadow: const [
                                BoxShadow(
                                  color: Color(0x200D365A),
                                  blurRadius: 16,
                                  offset: Offset(0, 6),
                                ),
                              ],
                            ),
                            child: Row(
                              children: [
                                Text('Selected \\${_selected.length}'),
                                const Spacer(),
                                IconButton(
                                  onPressed: _busy ? null : _downloadSelection,
                                  icon: const Icon(Icons.download_rounded),
                                  tooltip: 'Download',
                                ),
                                IconButton(
                                  onPressed: _busy ? null : _deleteSelection,
                                  icon: const Icon(Icons.delete_rounded),
                                  tooltip: 'Delete',
                                ),
                                IconButton(
                                  onPressed: _busy
                                      ? null
                                      : () => setState(_selected.clear),
                                  icon: const Icon(Icons.close_rounded),
                                  tooltip: 'Clear selection',
                                ),
                              ],
                            ),
                          )
                        : const SizedBox.shrink(),
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
"""
if old_bottom not in text:
    raise SystemExit("bottom block not found")
text = text.replace(old_bottom, new_bottom, 1)

path.write_text(text, encoding="utf-8")
print("patched")
