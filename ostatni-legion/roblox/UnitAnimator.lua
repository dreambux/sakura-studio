--!nonstrict
-- UnitAnimator (ModuleScript, po stronie klienta)
--
-- Odtwarza klatki z Blendera (UnitData.<Jednostka>) na Motor6D.Transform rigu zbudowanego przez
-- RigBuilder. Transform nie replikuje sie, wiec kazdy klient animuje u siebie.
--
--   local UnitAnimator = require(ReplicatedStorage.OstatniLegion.UnitAnimator)
--   local anim = UnitAnimator.new(towerModel, require(UnitData.Legionista))
--   anim:On("Hit", function(ev) ... end)          -- trafienie / wystrzal (ev.Frame, ev.Projectile...)
--   anim:PlayAttack(UnitAnimator.AttackForLevel(level))   -- na sygnal UnitAttack z serwera
--   anim:Destroy()                                  -- przy sprzedazy jednostki
--
-- Wbudowane zdarzenia z danych: Hide/Show (chowa np. wyrzucone pilum), TrailOn/TrailOff (smuga
-- "Swoosh" miedzy dwoma Attachmentami). Reszta (Hit, Shoot...) trafia do callbackow On().

local RunService = game:GetService("RunService")

local BLEND_FRAMES = 3

export type Clip = {
	Label: string,
	Loop: boolean,
	Length: number,
	Level: string,
	Events: {any},
	Tracks: {[string]: {number}},
}

local UnitAnimator = {}
UnitAnimator.__index = UnitAnimator

function UnitAnimator.AttackForLevel(level: number): string
	if level >= 4 then
		return "Attack3"
	elseif level >= 2 then
		return "Attack2"
	end
	return "Attack1"
end

local function sample(track: {number}, f: number, length: number, loop: boolean, scale: number): CFrame
	local i0 = math.floor(f)
	local a = f - i0
	local i1 = i0 + 1
	if loop then
		i0 %= length
		i1 %= length
	else
		i0 = math.clamp(i0, 0, length)
		i1 = math.clamp(i1, 0, length)
	end
	local b0 = i0 * 7
	local b1 = i1 * 7
	local c0 = CFrame.new(track[b0 + 1] * scale, track[b0 + 2] * scale, track[b0 + 3] * scale,
		track[b0 + 4], track[b0 + 5], track[b0 + 6], track[b0 + 7])
	if a < 1e-4 then
		return c0
	end
	local c1 = CFrame.new(track[b1 + 1] * scale, track[b1 + 2] * scale, track[b1 + 3] * scale,
		track[b1 + 4], track[b1 + 5], track[b1 + 6], track[b1 + 7])
	return c0:Lerp(c1, a)
end

function UnitAnimator.new(model: Model, data: any)
	local self = setmetatable({}, UnitAnimator)
	self.Model = model
	self.Data = data
	self.Fps = data.Fps or 30
	self.Motors = {} :: {[string]: Motor6D}
	self.Anchors = {} :: {[string]: BasePart}
	for _, d in model:GetDescendants() do
		if d:IsA("Motor6D") and d.Part1 then
			self.Motors[d.Part1.Name] = d
		end
	end
	for _, j in data.Joints do
		local p = model:FindFirstChild(j.Name)
		if p and p:IsA("BasePart") then
			self.Anchors[j.Name] = p
		end
	end
	self.Callbacks = {} :: {[string]: {(any, any) -> ()}}
	self.Trails = {} :: {Trail}
	self.ClipName = ""
	self.Time = 0
	self.From = {} :: {[string]: CFrame}
	self.BlendT = 1
	self.Queue = nil :: string?
	self:Play("Idle")
	self.Conn = RunService.RenderStepped:Connect(function(dt)
		self:_step(dt)
	end)
	return self
end

function UnitAnimator:On(eventName: string, fn: (any, any) -> ())
	self.Callbacks[eventName] = self.Callbacks[eventName] or {}
	table.insert(self.Callbacks[eventName], fn)
end

function UnitAnimator:_scale(): number
	return (self.Model:GetAttribute("RigScale") or 1) * self.Model:GetScale()
end

function UnitAnimator:Play(name: string)
	local clip = self.Data.Clips[name]
	if not clip then
		warn("UnitAnimator: brak klipu", name)
		return
	end
	-- zapamietaj aktualna poze do plynnego przejscia
	for jn, m in self.Motors do
		self.From[jn] = m.Transform
	end
	self.BlendT = 0
	self.ClipName = name
	self.Time = 0
	self.LastFrame = -1
	self:_setTrails(false)
	for jn in self.Motors do
		self:_setHidden(jn, false)
	end
end

function UnitAnimator:PlayAttack(name: string)
	self:Play(name)
	self.Queue = "Idle"
end

function UnitAnimator:_setHidden(joint: string, hidden: boolean)
	for _, p in self.Model:GetChildren() do
		if p:IsA("BasePart") and string.sub(p.Name, 1, #joint + 2) == joint .. "__" then
			p.LocalTransparencyModifier = hidden and 1 or 0
		end
	end
end

function UnitAnimator:_setTrails(on: boolean, ev: any?)
	if on and ev then
		local a0 = self.Model:FindFirstChild(ev.A, true)
		local a1 = self.Model:FindFirstChild(ev.B, true)
		if a0 and a1 and a0:IsA("Attachment") and a1:IsA("Attachment") then
			local t = Instance.new("Trail")
			t.Name = "Swoosh"
			t.Attachment0 = a0
			t.Attachment1 = a1
			t.Lifetime = 0.18
			t.MinLength = 0
			t.FaceCamera = false
			t.LightEmission = 0.6
			t.Color = ColorSequence.new(Color3.fromRGB(225, 235, 255))
			t.Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 0.15),
				NumberSequenceKeypoint.new(1, 1),
			})
			t.Parent = a0.Parent
			table.insert(self.Trails, t)
		end
	else
		for _, t in self.Trails do
			t.Enabled = false
			task.delay(0.3, function()
				t:Destroy()
			end)
		end
		self.Trails = {}
	end
end

function UnitAnimator:_fire(ev: any)
	if ev.Name == "Hide" then
		self:_setHidden(ev.Joint, true)
	elseif ev.Name == "Show" then
		self:_setHidden(ev.Joint, false)
	elseif ev.Name == "TrailOn" then
		self:_setTrails(true, ev)
	elseif ev.Name == "TrailOff" then
		self:_setTrails(false)
	end
	local list = self.Callbacks[ev.Name]
	if list then
		for _, fn in list do
			task.spawn(fn, ev, self)
		end
	end
end

function UnitAnimator:_step(dt: number)
	local clip: Clip? = self.Data.Clips[self.ClipName]
	if not clip then
		return
	end
	self.Time += dt
	local f = self.Time * self.Fps
	if f >= clip.Length then
		if clip.Loop then
			self.Time %= clip.Length / self.Fps
			f = self.Time * self.Fps
			self.LastFrame = -1
		elseif self.Queue then
			local q = self.Queue
			self.Queue = nil
			self:Play(q)
			return
		else
			f = clip.Length
		end
	end
	-- zdarzenia przekroczone w tej klatce
	local cur = math.floor(f)
	if cur ~= self.LastFrame then
		for _, ev in clip.Events do
			if ev.Frame > self.LastFrame and ev.Frame <= cur then
				self:_fire(ev)
			end
		end
		self.LastFrame = cur
	end
	local scale = self:_scale()
	self.BlendT = math.min(1, self.BlendT + dt * self.Fps / BLEND_FRAMES)
	for jn, m in self.Motors do
		local track = clip.Tracks[jn]
		local cf = if track then sample(track, f, clip.Length, clip.Loop, scale) else CFrame.identity
		if self.BlendT < 1 then
			cf = (self.From[jn] or CFrame.identity):Lerp(cf, self.BlendT)
		end
		m.Transform = cf
	end
end

function UnitAnimator:Destroy()
	if self.Conn then
		self.Conn:Disconnect()
		self.Conn = nil
	end
	self:_setTrails(false)
end

return UnitAnimator
