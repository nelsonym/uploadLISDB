-- table_layout.lua
-- Heuristic table handling:
-- - Keep row 1 as header if it contains bold/bold-italic text.
-- - Keep "box tables" as raw HTML for layout preservation.

local stringify = pandoc.utils.stringify

local function inlines_have_bold(inlines)
  for _, inline in ipairs(inlines or {}) do
    if inline.t == "Strong" then
      return true
    end
    if inline.t == "Emph" then
      for _, inner in ipairs(inline.content or {}) do
        if inner.t == "Strong" then
          return true
        end
      end
    end
  end
  return false
end

local function cell_has_bold(cell)
  for _, block in ipairs(cell.contents or {}) do
    if block.t == "Para" or block.t == "Plain" then
      if inlines_have_bold(block.content) then
        return true
      end
    end
  end
  return false
end

local function row_has_bold(row)
  for _, cell in ipairs(row.cells or {}) do
    if cell_has_bold(cell) then
      return true
    end
  end
  return false
end

local function looks_like_box_table(tbl)
  if #tbl.bodies == 0 then
    return false
  end
  local body = tbl.bodies[1]
  if #body.body == 0 then
    return false
  end
  local first_row = body.body[1]
  if #first_row.cells == 1 then
    return true
  end
  return false
end

local function escape_html(text)
  return text
    :gsub("&", "&amp;")
    :gsub("<", "&lt;")
    :gsub(">", "&gt;")
end

local function table_to_html(tbl)
  local parts = {"<table>"}
  if #tbl.bodies > 0 then
    for _, body in ipairs(tbl.bodies) do
      for _, row in ipairs(body.body or {}) do
        table.insert(parts, "<tr>")
        for _, cell in ipairs(row.cells or {}) do
          local content = {}
          for _, block in ipairs(cell.contents or {}) do
            content[#content + 1] = escape_html(stringify(block))
          end
          parts[#parts + 1] = "<td>" .. table.concat(content, "<br />") .. "</td>"
        end
        parts[#parts + 1] = "</tr>"
      end
    end
  end
  parts[#parts + 1] = "</table>"
  return pandoc.RawBlock("html", table.concat(parts, "\n"))
end

function Table(tbl)
  if looks_like_box_table(tbl) then
    return table_to_html(tbl)
  end

  if #tbl.bodies > 0 then
    local body = tbl.bodies[1]
    if #body.body > 0 and row_has_bold(body.body[1]) then
      tbl.head = pandoc.TableHead({ body.body[1] })
      table.remove(body.body, 1)
      tbl.bodies[1] = body
      return tbl
    end
  end

  return tbl
end
