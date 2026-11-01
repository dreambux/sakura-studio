--!nonstrict
-- MapLighting (ModuleScript) - "shadery" map Ostatniego Legionu.
-- W Robloxie nie ma wlasnych shaderow GLSL, klimat robi sie efektami Lighting:
-- Atmosphere (mgla/haze/blask), Bloom, ColorCorrection, SunRays, DepthOfField, Clouds,
-- kolor wody terenu i czasteczki w powietrzu. Kazda mapa ma wlasny preset.
--
--   local MapLighting = require(game.ReplicatedStorage.OstatniLegion.MapLighting)
--   MapLighting.Apply("ZatokaPireusu")   -- albo LabiryntKnossos / ZboczaOlimpu / KuzniaHefajstosa

local Lighting = game:GetService("Lighting")

local MapLighting = {}

local function c(r, g, b)
	return Color3.fromRGB(r, g, b)
end

MapLighting.Presets = {
	-- 1. Slonce w poludnie nad turkusowym portem
	ZatokaPireusu = {
		Lighting = {
			ClockTime = 13.2, GeographicLatitude = 38, Brightness = 3.2, ExposureCompensation = 0.1,
			Ambient = c(96, 92, 100), OutdoorAmbient = c(150, 146, 150),
			ColorShift_Top = c(255, 238, 214), ColorShift_Bottom = c(120, 160, 190),
			EnvironmentDiffuseScale = 1, EnvironmentSpecularScale = 1, ShadowSoftness = 0.15,
		},
		Atmosphere = {Density = 0.27, Offset = 0.12, Color = c(199, 222, 236), Decay = c(104, 146, 168), Glare = 0.25, Haze = 1.1},
		Bloom = {Intensity = 0.55, Size = 24, Threshold = 1.7},
		ColorCorrection = {Brightness = 0.02, Contrast = 0.08, Saturation = 0.14, TintColor = c(255, 250, 240)},
		SunRays = {Intensity = 0.05, Spread = 0.6},
		Clouds = {Cover = 0.45, Density = 0.45, Color = c(255, 255, 255)},
		Water = {WaterColor = c(22, 138, 150), WaterTransparency = 0.55, WaterReflectance = 0.65, WaterWaveSize = 0.16, WaterWaveSpeed = 12},
	},
	-- 2. Zlota godzina nad palacem minojskim
	LabiryntKnossos = {
		Lighting = {
			ClockTime = 17.7, GeographicLatitude = 35, Brightness = 2.6, ExposureCompensation = 0.15,
			Ambient = c(110, 84, 70), OutdoorAmbient = c(160, 120, 96),
			ColorShift_Top = c(255, 200, 140), ColorShift_Bottom = c(140, 90, 70),
			EnvironmentDiffuseScale = 1, EnvironmentSpecularScale = 0.8, ShadowSoftness = 0.25,
		},
		Atmosphere = {Density = 0.33, Offset = 0.2, Color = c(255, 196, 150), Decay = c(196, 112, 82), Glare = 0.7, Haze = 1.7},
		Bloom = {Intensity = 0.85, Size = 32, Threshold = 1.4},
		ColorCorrection = {Brightness = 0.02, Contrast = 0.1, Saturation = 0.16, TintColor = c(255, 233, 206)},
		SunRays = {Intensity = 0.12, Spread = 0.75},
		Clouds = {Cover = 0.38, Density = 0.4, Color = c(255, 214, 186)},
		Water = {WaterColor = c(30, 96, 118), WaterTransparency = 0.5, WaterReflectance = 0.8, WaterWaveSize = 0.12, WaterWaveSpeed = 9},
	},
	-- 3. Chlodne, krystaliczne swiatlo nad chmurami
	ZboczaOlimpu = {
		Lighting = {
			ClockTime = 10.4, GeographicLatitude = 40, Brightness = 3.4, ExposureCompensation = 0.05,
			Ambient = c(100, 108, 126), OutdoorAmbient = c(150, 160, 186),
			ColorShift_Top = c(240, 246, 255), ColorShift_Bottom = c(150, 170, 210),
			EnvironmentDiffuseScale = 1, EnvironmentSpecularScale = 1, ShadowSoftness = 0.1,
		},
		Atmosphere = {Density = 0.24, Offset = 0.0, Color = c(222, 234, 255), Decay = c(150, 172, 214), Glare = 0.45, Haze = 0.7},
		Bloom = {Intensity = 0.6, Size = 28, Threshold = 1.5},
		ColorCorrection = {Brightness = 0.03, Contrast = 0.12, Saturation = 0.06, TintColor = c(242, 248, 255)},
		SunRays = {Intensity = 0.16, Spread = 0.85},
		Clouds = {Cover = 0.72, Density = 0.62, Color = c(255, 255, 255)},
		DepthOfField = {FarIntensity = 0.12, FocusDistance = 140, InFocusRadius = 120, NearIntensity = 0},
		Water = {WaterColor = c(60, 150, 190), WaterTransparency = 0.7, WaterReflectance = 0.5, WaterWaveSize = 0.08, WaterWaveSpeed = 18},
	},
	-- 4. Noc, lawa i zar w powietrzu
	KuzniaHefajstosa = {
		Lighting = {
			ClockTime = 0.3, GeographicLatitude = 36, Brightness = 1.4, ExposureCompensation = 0.25,
			Ambient = c(54, 28, 26), OutdoorAmbient = c(82, 46, 46),
			ColorShift_Top = c(255, 120, 70), ColorShift_Bottom = c(80, 20, 10),
			EnvironmentDiffuseScale = 0.6, EnvironmentSpecularScale = 1, ShadowSoftness = 0.35,
		},
		Atmosphere = {Density = 0.45, Offset = 0.25, Color = c(126, 44, 34), Decay = c(60, 12, 10), Glare = 0, Haze = 2.6},
		Bloom = {Intensity = 1.25, Size = 40, Threshold = 0.9},
		ColorCorrection = {Brightness = -0.02, Contrast = 0.2, Saturation = 0.12, TintColor = c(255, 206, 194)},
		SunRays = {Intensity = 0.0, Spread = 0.5},
		Clouds = {Cover = 0.82, Density = 0.7, Color = c(70, 34, 32)},
		Water = {WaterColor = c(12, 22, 28), WaterTransparency = 0.25, WaterReflectance = 0.9, WaterWaveSize = 0.2, WaterWaveSpeed = 6},
		Embers = {Color = c(255, 120, 40), Rate = 45},
	},
}

local TAG = "OstatniLegionFx"

local function make(className, parent, props)
	local inst = parent:FindFirstChild(TAG .. className)
	if not inst then
		inst = Instance.new(className)
		inst.Name = TAG .. className
		inst.Parent = parent
	end
	for k, v in props do
		pcall(function()
			inst[k] = v
		end)
	end
	return inst
end

function MapLighting.Apply(name: string, mapCenter: Vector3?)
	local p = MapLighting.Presets[name]
	assert(p, "MapLighting: brak presetu " .. tostring(name))
	pcall(function()
		Lighting.Technology = Enum.Technology.Future
	end)
	Lighting.GlobalShadows = true
	for k, v in p.Lighting do
		pcall(function()
			Lighting[k] = v
		end)
	end
	make("Atmosphere", Lighting, p.Atmosphere)
	make("BloomEffect", Lighting, p.Bloom)
	make("ColorCorrectionEffect", Lighting, p.ColorCorrection)
	make("SunRaysEffect", Lighting, p.SunRays)
	local dof = Lighting:FindFirstChild(TAG .. "DepthOfFieldEffect")
	if p.DepthOfField then
		make("DepthOfFieldEffect", Lighting, p.DepthOfField)
	elseif dof then
		dof:Destroy()
	end
	local terrain = workspace.Terrain
	make("Clouds", terrain, p.Clouds)
	for k, v in p.Water do
		pcall(function()
			terrain[k] = v
		end)
	end
	-- zar w powietrzu (Kuznia)
	local old = workspace:FindFirstChild(TAG .. "Embers")
	if old then
		old:Destroy()
	end
	if p.Embers then
		local part = Instance.new("Part")
		part.Name = TAG .. "Embers"
		part.Anchored = true
		part.CanCollide = false
		part.CanQuery = false
		part.Transparency = 1
		part.Size = Vector3.new(240, 1, 200)
		part.CFrame = CFrame.new((mapCenter or Vector3.zero) + Vector3.new(0, 2, 0))
		local pe = Instance.new("ParticleEmitter")
		pe.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		pe.Color = ColorSequence.new(p.Embers.Color)
		pe.LightEmission = 1
		pe.Rate = p.Embers.Rate
		pe.Lifetime = NumberRange.new(4, 8)
		pe.Speed = NumberRange.new(2, 6)
		pe.SpreadAngle = Vector2.new(25, 25)
		pe.EmissionDirection = Enum.NormalId.Top
		pe.Size = NumberSequence.new({NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0)})
		pe.Acceleration = Vector3.new(0, 1.5, 0)
		pe.Parent = part
		part.Parent = workspace
	end
end

return MapLighting
