--!strict
-- RigBuilder (ModuleScript, np. ReplicatedStorage.OstatniLegion.RigBuilder)
--
-- Sklada model zaimportowany z GLB (export/<Jednostka>/<Jednostka>.glb) w rig na Motor6D
-- wedlug danych z <Jednostka>_UnitData.lua. Uruchom raz w Studio (pasek polecen albo plugin),
-- potem zapisz gotowy model do TowerModels.
--
-- Czesci z GLB nazywaja sie "<Joint>__<material>" (np. "Right Arm__steel").
-- Dla kazdego jointu powstaje niewidoczna czesc-kotwica o nazwie jointu w jego punkcie obrotu
-- (osie jak model), czesci z GLB sa do niej przyspawane (WeldConstraint), a kotwice lacza
-- Motor6D: C0 = przesuniecie od rodzica, C1 = identycznosc. Dzieki temu klatki z Blendera
-- to dokladnie Motor6D.Transform.
--
-- Uzycie (pasek polecen w Studio):
--   local RB = require(game.ReplicatedStorage.OstatniLegion.RigBuilder)
--   local data = require(game.ReplicatedStorage.OstatniLegion.UnitData.Legionista)
--   RB.Build(workspace.Legionista, data)
--   workspace.Legionista:ScaleTo(0.55)

local RigBuilder = {}

local function v3(t: {number}): Vector3
	return Vector3.new(t[1], t[2], t[3])
end

local function jointOf(name: string): string?
	return string.match(name, "^(.-)__")
end

function RigBuilder.Build(model: Model, data: any): Model
	local meshes: {BasePart} = {}
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and jointOf(d.Name) then
			table.insert(meshes, d)
		end
	end
	assert(#meshes > 0, "RigBuilder: brak czesci o nazwach '<Joint>__<material>' w modelu")

	-- skala i polozenie: porownanie bounding boxa z danymi (odporne na skale i przesuniecie importu)
	local bbCf, bbSize = model:GetBoundingBox()
	local bMin = v3(data.Bounds.Min)
	local bMax = v3(data.Bounds.Max)
	local dSize = bMax - bMin
	local s = bbSize.Y / dSize.Y
	local rot = bbCf.Rotation
	local function toWorld(p: Vector3): Vector3
		local localPos = -bbSize / 2 + (p - bMin) * s
		return bbCf:PointToWorldSpace(localPos)
	end

	-- kotwice jointow
	local anchors: {[string]: BasePart} = {}
	for _, j in data.Joints do
		local a = Instance.new("Part")
		a.Name = j.Name
		a.Size = Vector3.one * 0.2 * s
		a.Transparency = 1
		a.CanCollide = false
		a.CanQuery = false
		a.CanTouch = false
		a.Massless = true
		a.Anchored = j.Parent == nil
		a.CFrame = rot + toWorld(v3(j.Pivot))
		a.Parent = model
		anchors[j.Name] = a
	end

	-- czesci z GLB -> spawane do kotwic
	for _, p in meshes do
		local jn = jointOf(p.Name) :: string
		local a = anchors[jn]
		if a then
			p.Anchored = false
			p.CanCollide = false
			p.Massless = true
			p.Parent = model
			local w = Instance.new("WeldConstraint")
			w.Part0 = a
			w.Part1 = p
			w.Parent = a
		else
			warn("RigBuilder: nieznany joint", jn, "dla", p.Name)
		end
	end

	-- Motor6D
	for _, j in data.Joints do
		if j.Parent then
			local p0 = anchors[j.Parent]
			local p1 = anchors[j.Name]
			local m = Instance.new("Motor6D")
			m.Name = j.Name
			m.Part0 = p0
			m.Part1 = p1
			m.C0 = p0.CFrame:ToObjectSpace(p1.CFrame)
			m.C1 = CFrame.identity
			m.Parent = p0
		end
	end

	-- punkty efektow (smuga, pociski, promienie)
	for name, a in data.Attachments do
		local anchor = anchors[a.Joint]
		if anchor then
			local att = Instance.new("Attachment")
			att.Name = name
			att.Position = v3(a.Offset) * s
			att.Parent = anchor
		end
	end

	-- puste foldery po imporcie
	for _, d in model:GetChildren() do
		if (d:IsA("Model") or d:IsA("Folder")) and #d:GetDescendants() == 0 then
			d:Destroy()
		end
	end

	model.PrimaryPart = anchors.HumanoidRootPart
	model:SetAttribute("RigScale", s)
	model:SetAttribute("UnitName", data.Name)
	return model
end

return RigBuilder
