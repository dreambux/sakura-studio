--!nonstrict
-- MapBuilder (ModuleScript) - stawia mape z konceptu (maps/koncepty/<nr>_<Mapa>_uklad.lua).
--
-- Przygotowanie w Studio:
--   1. Zaimportuj paczki modeli maps/modele/<Kategoria>.glb (3D Importer) i wrzuc wszystkie modele
--      do jednego folderu, np. ServerStorage.MapAssets (kazdy model nazywa sie jak w katalogu, np. "cyprys").
--   2. Wrzuc uklad mapy jako ModuleScript (np. ServerStorage.MapLayouts.ZatokaPireusu).
--   3. W pasku polecen:
--        local MB = require(game.ReplicatedStorage.OstatniLegion.MapBuilder)
--        MB.Build(require(game.ServerStorage.MapLayouts.ZatokaPireusu), game.ServerStorage.MapAssets)
--      Powstaje workspace.Map z folderami Props, Waypoints (1..N), WaypointsB, WaypointsC ...
--   4. Teren/sciezki dorob wedlug renderu konceptu (albo zaimportuj <nr>_<Mapa>_teren.glb jako podglad),
--      klimat: MapLighting.Apply("<Nazwa>").
--
-- Kazdy model z GLB ma poczatek ukladu na srodku podstawy (0,0,0). Builder ustawia WorldPivot na ten punkt,
-- uwzgledniajac skale importu (porownanie z katalogiem bbox z maps/modele/katalog.json, jesli podasz Catalog).

local CollectionService = game:GetService("CollectionService")

local MapBuilder = {}

local function v3(t)
	return Vector3.new(t[1], t[2], t[3])
end

-- Ustaw pivot modelu na srodek podstawy (najnizszy punkt, srodek w XZ) - tak wyeksportowane sa modele.
local function prepare(model: Model)
	if model:GetAttribute("OL_Prepared") then
		return
	end
	local cf, size = model:GetBoundingBox()
	local base = cf.Position - Vector3.new(0, size.Y / 2, 0)
	model.WorldPivot = CFrame.new(base)
	model:SetAttribute("OL_Prepared", true)
end

function MapBuilder.Build(layout, assets: Instance, parent: Instance?)
	parent = parent or workspace
	local old = parent:FindFirstChild("Map")
	if old then
		old:Destroy()
	end
	local map = Instance.new("Model")
	map.Name = "Map"
	map:SetAttribute("MapName", layout.Name)
	map:SetAttribute("Difficulty", layout.Difficulty)
	local props = Instance.new("Folder")
	props.Name = "Props"
	props.Parent = map

	local missing = {}
	for _, p in layout.Props do
		local name, x, y, z, rot, scale = p[1], p[2], p[3], p[4], p[5], p[6]
		local src = assets:FindFirstChild(name, true)
		if not src then
			missing[name] = (missing[name] or 0) + 1
			continue
		end
		local m = src:Clone()
		if m:IsA("Model") then
			prepare(m)
			if scale and math.abs(scale - 1) > 0.001 then
				m:ScaleTo(m:GetScale() * scale)
			end
			m:PivotTo(CFrame.new(x, y, z) * CFrame.Angles(0, math.rad(rot), 0))
			for _, d in m:GetDescendants() do
				if d:IsA("BasePart") then
					d.Anchored = true
				end
			end
		elseif m:IsA("BasePart") then
			m.Anchored = true
			m.CFrame = CFrame.new(x, y, z) * CFrame.Angles(0, math.rad(rot), 0)
		end
		CollectionService:AddTag(m, "LG_Decor")
		m.Parent = props
	end

	-- waypointy (jak na mapie testowej: Waypoints / WaypointsB / WaypointsC, czesci "1".."N")
	local suffix = {"", "B", "C", "D"}
	for i, path in layout.Paths do
		local f = Instance.new("Folder")
		f.Name = "Waypoints" .. (suffix[i] or tostring(i))
		f:SetAttribute("Label", path.Label)
		f:SetAttribute("Width", path.Width)
		-- co drugi punkt wystarczy (sciezka w danych jest wygladzona)
		local n = 0
		for k, pt in path.Points do
			if k == 1 or k == #path.Points or k % 3 == 0 then
				n += 1
				local wp = Instance.new("Part")
				wp.Name = tostring(n)
				wp.Anchored = true
				wp.CanCollide = false
				wp.CanQuery = false
				wp.Transparency = 1
				wp.Size = Vector3.new(1, 1, 1)
				wp.Position = v3(pt)
				wp.Parent = f
			end
		end
		f.Parent = map
	end
	map.Parent = parent
	for name, count in missing do
		warn(("MapBuilder: brak modelu '%s' w assets (%d szt.)"):format(name, count))
	end
	return map
end

return MapBuilder
