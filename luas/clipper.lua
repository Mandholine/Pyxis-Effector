	--[[
	The Clipper library performs clipping and offsetting for both lines and polygons. All four boolean
	clipping operations are supported - intersection, union, difference and exclusive-or. Polygons can
	be of any shape including self-intersecting polygons. Clipping: In 2-dimensional geometry, clipping
	commonly refers to the process of removing those geometric objects, or parts of objects, that appear
	outside a rectangular 'clipping' window. Since geometric objects are typically represented by series
	of paths (lines and polygons), clipping is achieved by intersecting these paths with a clipping
	rectangle. In a more general sense, the clipping window need not be rectangular but can be any type
	of polygon, even multiple polygons. Also, while clipping typically refers to an intersection operation,
	in this documentation it will refer to any one of the four boolean operations (intersection, union,
	difference and exclusive-or). By Angus Johnson. Copyright © 2010-2022. This library was translated
	into the LUA programming language thanks to the hard work of my good friend Zeref Sama. I will always
	be grateful for his hard work. :D
	--]]
	
	local class = {
		create = function(class_name, init, base)
			init = init or function() end
			base = base or {}
			base.__index = base
			local classe = setmetatable(
				{
					__name = class_name,
					__init = init,
					__base = base
				},
				{
					__index = base,
					__call = function(cls, ...)
						local _self = setmetatable({}, base)
						cls.__init(_self, ...)
						return _self
					end
				}
			)
			base.__class = classe
			return classe
		end,

		extends = function(class, class_name, init, base)
			local _parent = class
			init = init or function() end
			base = base or {}
			base.__index = base
			setmetatable(base, _parent.__base)
			local classe = setmetatable(
				{
					__init = init,
					__base = base,
					__name = class_name,
					__parent = _parent
				},
				{
					__index = function(cls, name)
						local val = rawget(base, name)
						if val == nil then
							local parent = rawget(cls, "__parent")
							if parent then
								return parent[name]
							end
						else
							return val
						end
					end,
					__call = function(cls, ...)
						local _self = setmetatable({}, base)
						cls.__init(_self, ...)
						return _self
					end
				}
			)
			base.__class = classe
			if _parent.__inherited then
				_parent.__inherited(_parent, classe)
			end
			return classe
		end
	}

	local ClipperLib = {
		use_lines = true,
		Clear = function()
			return {}
		end,
		PI = 3.141592653589793,
		PI2 = 2 * 3.141592653589793,
		ClipType = {
			ctIntersection = 0,
			ctUnion = 1,
			ctDifference = 2,
			ctXor = 3
		},
		PolyType = {
			ptSubject = 0,
			ptClip = 1
		},
		PolyFillType = {
			pftEvenOdd = 0,
			pftNonZero = 1,
			pftPositive = 2,
			pftNegative = 3
		},
		JoinType = {
			jtSquare = 0,
			jtRound = 1,
			jtMiter = 2
		},
		EndType = {
			etOpenSquare = 0,
			etOpenRound = 1,
			etOpenButt = 2,
			etClosedLine = 3,
			etClosedPolygon = 4
		},
		EdgeSide = {
			esLeft = 0,
			esRight = 1
		},
		Direction = {
			dRightToLeft = 0,
			dLeftToRight = 1
		},
		Point = {},
		ClipperBase = {
			horizontal = -9007199254740992,
			Skip = -2,
			Unassigned = -1,
			tolerance = 1E-20,
			loRange = 47453132,
			hiRange = 4503599627370495
		},
		Clipper = {
			ioReverseSolution = 1,
			ioStrictlySimple = 2,
			ioPreserveCollinear = 4,
			NodeType = {
				ntAny = 0,
				ntOpen = 1,
				ntClosed = 2
			}
		},
		rDecimals = 2,
		MyIntersectNodeSort = {},
		ClipperOffset = {
			two_pi = 6.28318530717959,
			def_arc_tolerance = 0.25
		}
	}

	local BitXOR = function(a, b)
		local p, c = 1, 0
		while a > 0 and b > 0 do
			local ra, rb = a % 2, b % 2
			if ra ~= rb then
				c = c + p
			end
			a, b, p = (a - ra) / 2, (b - rb) / 2, p * 2
		end
		a = a < b and b or a
		while a > 0 do
			local ra = a % 2
			if ra > 0 then
				c = c + p
			end
			a, p = (a - ra) / 2, p * 2
		end
		return c
	end

	--CLASS PATH
	local Path = class.create("Path")

	--CLASS POLYNODE
	local PolyNode = class.create("PolyNode",
		function(self)
			self.m_Parent = nil
			self.m_polygon = Path()
			self.m_Index = 0
			self.m_jointype = 0
			self.m_endtype = 0
			self.m_Childs = {}
			self.IsOpen = false
		end,
		{
			m_Childs = {},

			IsHoleNode = function(self)
				local result = true
				local node = self.m_Parent
				while node ~= nil do
					result = not result
					node = node.m_Parent
				end
				return result
			end,

			ChildCount = function(self)
				return #self.m_Childs
			end,

			Contour = function(self)
				return self.m_polygon
			end,

			AddChild = function(self, Child)
				local cnt = #self.m_Childs
				table.insert(self.m_Childs, Child)
				Child.m_Parent = self
				Child.m_Index = cnt
			end,

			GetNext = function(self)
				if #self.m_Childs > 1 then
					return self.m_Childs[1]
				else
					return self:GetNextSiblingUp()
				end
			end,

			GetNextSiblingUp = function(self)
				if self.m_Parent == nil then
					return nil
				elseif self.m_Index == #self.m_Parent.m_Childs then
					return self.m_Parent:GetNextSiblingUp()
				else
					return self.m_Parent.m_Childs[self.m_Index + 1]
				end
			end,

			Childs = function(self)
				return self.m_Childs
			end,

			Parent = function(self)
				return self.m_Parent
			end,

			IsHole = function(self)
				return self:IsHoleNode()
			end

		}
	)

	--CLASS POINT
	local Point = class.create("Point",
		function(self, ...)
			local a = {...}
			self.x, self.y = 0, 0
			if #a == 1 then
				self.x, self.y = a[1].x, a[1].y
			elseif #a == 2 then
				self.x, self.y = a[1], a[2]
			end
		end
	)

	--CLASS RECT
	local Rect = class.create("Rect",
		function(self, ...)
			local a = {...}
			self.left, self.top, self.right, self.bottom = 0, 0, 0, 0
			if #a == 4 then
				self.left, self.top, self.right, self.bottom = a[1], a[2], a[3], a[4]
			elseif #a == 1 then
				self.left, self.top, self.right, self.bottom = a[1].left, a[1].top, a[1].right, a[1].bottom
			end
		end
	)

	--CLASS TEDGE
	local TEdge = class.create("TEdge",
		function(self)
			self.Bot = Point()
			self.Curr = Point() --current (updated for every new scanbeam)
			self.Top = Point()
			self.Delta = Point()
			self.Dx = 0
			self.PolyTyp = ClipperLib.PolyType.ptSubject
			self.Side = ClipperLib.EdgeSide.esLeft --side only refers to current side of solution poly
			self.WindDelta = 0 --1 or -1 depending on winding direction
			self.WindCnt = 0
			self.WindCnt2 = 0 --winding count of the opposite polytype
			self.OutIdx = 0
			self.Next = nil
			self.Prev = nil
			self.NextInLML = nil
			self.NextInAEL = nil
			self.PrevInAEL = nil
			self.NextInSEL = nil
			self.PrevInSEL = nil
		end
	)

	--CLASS INTERSECTEDNODE
	local IntersectNode = class.create("IntersectNode",
		function(self)
			self.Edge1 = nil
			self.Edge2 = nil
			self.Pt = Point()
		end
	)

	--CLASS LOCALMINIMA
	local LocalMinima = class.create("LocalMinima",
		function(self)
			self.y = 0
			self.LeftBound = nil
			self.RightBound = nil
			self.Next = nil
		end
	)

	--CLASS SCANBEAM
	local Scanbeam = class.create("Scanbeam",
		function(self)
			self.y = 0
			self.Next = nil
		end
	)

	--CLASS MAXIMA
	local Maxima = class.create("Maxima",
		function(self)
			self.x = 0
			self.Next = nil
			self.Prev = nil
		end
	)

	--CLASS OUTEREC
	local OutRec = class.create("OutRec",
		function(self)
			self.Idx = 0
			self.IsHole = false
			self.IsOpen = false
			self.FirstLeft = nil
			self.Pts = nil
			self.BottomPt = nil
			self.PolyNode = nil
		end
	)

	--CLASS OUTPT
	local OutPt = class.create("OutPt",
		function(self)
			self.Idx = 0
			self.Pt = Point()
			self.Next = nil
			self.Prev = nil
		end
	)

	--CLASS JOIN
	local Join = class.create("Join",
		function(self)
			self.OutPt1 = nil
			self.OutPt2 = nil
			self.OffPt = Point()
		end
	)

	--CLASS CLIPPERBASE
	local ClipperBase = class.create("ClipperBase", nil,
		{
			m_MinimaList = nil,
			m_CurrentLM = nil,
			m_edges = {},
			m_HasOpenPaths = false,
			PreserveCollinear = false,
			m_Scanbeam = nil,
			m_PolyOuts = nil,
			m_ActiveEdges = nil,

			PointIsVertex = function(self, pt, pp)
				local pp2 = pp
				while true do
					if ClipperLib.Point.op_Equality(pp2.Pt, pt) then
						return true
					end
					pp2 = pp2.Next
					if pp2 == pp then
						break
					end
				end
				return false
			end,

			Clear = function(self)
				self:DisposeLocalMinimaList()
				for i = 1, #self.m_edges do
					for j = 1, #self.m_edges[i] do
						self.m_edges[i][j] = nil
					end
					self.m_edges[i] = ClipperLib.Clear()
				end
				self.m_edges = ClipperLib.Clear()
				self.m_HasOpenPaths = false
			end,

			DisposeLocalMinimaList = function(self)
				while self.m_MinimaList ~= nil do
					local tmpLm = self.m_MinimaList.Next
					self.m_MinimaList = nil
					self.m_MinimaList = tmpLm
				end
				self.m_CurrentLM = nil
			end,

			InitEdge = function(self, e, eNext, ePrev, pt)
				e.Next = eNext
				e.Prev = ePrev
				e.Curr.x = pt.x
				e.Curr.y = pt.y
				e.OutIdx = -1
			end,

			InitEdge2 = function(self, e, polyType)
				if e.Curr.y >= e.Next.Curr.y then
					e.Bot.x = e.Curr.x
					e.Bot.y = e.Curr.y
					e.Top.x = e.Next.Curr.x
					e.Top.y = e.Next.Curr.y
				else
					e.Top.x = e.Curr.x
					e.Top.y = e.Curr.y
					e.Bot.x = e.Next.Curr.x
					e.Bot.y = e.Next.Curr.y
				end
				self:SetDx(e)
				e.PolyTyp = polyType
			end,

			FindNextLocMin = function(self, E)
				local E2 = nil
				while true do
					do
						while ClipperLib.Point.op_Inequality(E.Bot, E.Prev.Bot) or ClipperLib.Point.op_Equality(E.Curr, E.Top) do
							E = E.Next
						end
						if E.Dx ~= ClipperLib.ClipperBase.horizontal and E.Prev.Dx ~= ClipperLib.ClipperBase.horizontal then
							break
						end
						while E.Prev.Dx == ClipperLib.ClipperBase.horizontal do
							E = E.Prev
						end
						E2 = E
						while E.Dx == ClipperLib.ClipperBase.horizontal do
							E = E.Next
						end
						if E.Top.y == E.Prev.Bot.y then
							goto continue
						end
						if E2.Prev.Bot.x < E.Bot.x then
							E = E2
						end
						break
					end
					::continue::
				end
				return E
			end,

			ProcessBound = function(self, E, LeftBoundIsForward)
				local EStart = nil
				local Result = E
				local Horz = nil
				if Result.OutIdx == ClipperLib.ClipperBase.Skip then
					E = Result
					if LeftBoundIsForward then
						while E.Top.y == E.Next.Bot.y do
							E = E.Next
						end
						while E ~= Result and E.Dx == ClipperLib.ClipperBase.horizontal do
							E = E.Prev
						end
					else
						while E.Top.y == E.Prev.Bot.y do
							E = E.Prev
						end
						while E ~= Result and E.Dx == ClipperLib.ClipperBase.horizontal do
							E = E.Next
						end
					end
					if E == Result then
						if LeftBoundIsForward then
							Result = E.Next
						else
							Result = E.Prev
						end
					else
						if LeftBoundIsForward then
							E = Result.Next
						else
							E = Result.Prev
						end
						local locMin = LocalMinima()
						locMin.Next = nil
						locMin.y = E.Bot.y
						locMin.LeftBound = nil
						locMin.RightBound = E
						E.WindDelta = 0
						Result = self:ProcessBound(E, LeftBoundIsForward)
						self:InsertLocalMinima(locMin)
					end
					return Result
				end
				if E.Dx == ClipperLib.ClipperBase.horizontal then
					if LeftBoundIsForward then
						EStart = E.Prev
					else
						EStart = E.Next
					end
					if EStart.Dx == ClipperLib.ClipperBase.horizontal then
						if EStart.Bot.x ~= E.Bot.x and EStart.Top.x ~= E.Bot.x then
							self:ReverseHorizontal(E)
						end
					elseif EStart.Bot.x ~= E.Bot.x then
						self:ReverseHorizontal(E)
					end
				end
				EStart = E
				if LeftBoundIsForward then
					while Result.Top.y == Result.Next.Bot.y and Result.Next.OutIdx ~= ClipperLib.ClipperBase.Skip do
						Result = Result.Next
					end
					if Result.Dx == ClipperLib.ClipperBase.horizontal and Result.Next.OutIdx ~= ClipperLib.ClipperBase.Skip then
						Horz = Result
						while Horz.Prev.Dx == ClipperLib.ClipperBase.horizontal do
							Horz = Horz.Prev
						end
						if Horz.Prev.Top.x > Result.Next.Top.x then
							Result = Horz.Prev
						end
					end
					while E ~= Result do
						E.NextInLML = E.Next
						if E.Dx == ClipperLib.ClipperBase.horizontal and E ~= EStart and E.Bot.x ~= E.Prev.Top.x then
							self:ReverseHorizontal(E)
						end
						E = E.Next
					end
					if E.Dx == ClipperLib.ClipperBase.horizontal and E ~= EStart and E.Bot.x ~= E.Prev.Top.x then
						self:ReverseHorizontal(E)
					end
					Result = Result.Next
				else
					while Result.Top.y == Result.Prev.Bot.y and Result.Prev.OutIdx ~= ClipperLib.ClipperBase.Skip do
						Result = Result.Prev
					end
					if Result.Dx == ClipperLib.ClipperBase.horizontal and Result.Prev.OutIdx ~= ClipperLib.ClipperBase.Skip then
						Horz = Result
						while Horz.Next.Dx == ClipperLib.ClipperBase.horizontal do
							Horz = Horz.Next
						end
						if Horz.Next.Top.x == Result.Prev.Top.x or Horz.Next.Top.x > Result.Prev.Top.x then
							Result = Horz.Next
						end
					end
					while E ~= Result do
						E.NextInLML = E.Prev
						if E.Dx == ClipperLib.ClipperBase.horizontal and E ~= EStart and E.Bot.x ~= E.Next.Top.x then
							self:ReverseHorizontal(E)
						end
						E = E.Prev
					end
					if E.Dx == ClipperLib.ClipperBase.horizontal and E ~= EStart and E.Bot.x ~= E.Next.Top.x then
						self:ReverseHorizontal(E)
					end
					Result = Result.Prev
				end
				return Result
			end,

			AddPath = function(self, pg, polyType, Closed)
				if ClipperLib.use_lines then
					if not Closed and polyType == ClipperLib.PolyType.ptClip then
						ClipperLib.Error("AddPath: Open paths must be subject.")
					end
				else
					if not Closed then
						ClipperLib.Error("AddPath: Open paths have been disabled.")
					end
				end
				local highI = #pg
				if Closed then
					while highI > 1 and ClipperLib.Point.op_Equality(pg[highI], pg[1]) do
						highI = highI - 1
					end
				end
				while highI > 1 and ClipperLib.Point.op_Equality(pg[highI], pg[highI - 1]) do
					highI = highI - 1
				end
				if (Closed and highI < 3) or (not Closed and highI < 2) then
					return false
				end
				local edges = {}
				for i = 1, highI do
					table.insert(edges, TEdge())
				end
				local IsFlat = true
				edges[2].Curr.x = pg[2].x
				edges[2].Curr.y = pg[2].y
				self:InitEdge(edges[1], edges[2], edges[highI], pg[1])
				self:InitEdge(edges[highI], edges[1], edges[highI - 1], pg[highI])
				for i = highI - 1, 2, -1 do
					self:InitEdge(edges[i], edges[i + 1], edges[i - 1], pg[i])
				end
				local eStart = edges[1]
				local E = eStart
				local eLoopStop = eStart
				while true do
					if E.Curr == E.Next.Curr and (Closed or E.Next ~= eStart) then
						if E == E.Next then
							break
						end
						if E == eStart then
							eStart = E.Next
						end
						E = self:RemoveEdge(E)
						eLoopStop = E
						goto continue
					end
					if E.Prev == E.Next then
						break
					elseif (Closed and ClipperLib.ClipperBase.SlopesEqual(E.Prev.Curr, E.Curr, E.Next.Curr) and
						(not self.PreserveCollinear or self:Pt2IsBetweenPt1AndPt3(E.Prev.Curr, E.Curr, E.Next.Curr))) then
						if E == eStart then
							eStart = E.Next
						end
						E = self:RemoveEdge(E)
						E = E.Prev
						eLoopStop = E
						goto continue
					end
					E = E.Next
					if E == eLoopStop or (not Closed and E.Next == eStart) then
						break
					end
					::continue::
				end
				if ((not Closed and (E == E.Next)) or (Closed and (E.Prev == E.Next))) then
					return false
				end
				if not Closed then
					self.m_HasOpenPaths = true
					eStart.Prev.OutIdx = ClipperLib.ClipperBase.Skip
				end
				E = eStart
				while true do
					self:InitEdge2(E, polyType)
					E = E.Next
					if IsFlat and E.Curr.y ~= eStart.Curr.y then
						IsFlat = false
					end
					if E == eStart then
						break
					end
				end
				if IsFlat then
					if Closed then
						return false
					end
					E.Prev.OutIdx = ClipperLib.ClipperBase.Skip
					local locMin = LocalMinima()
					locMin.Next = nil
					locMin.y = E.Bot.y
					locMin.LeftBound = nil
					locMin.RightBound = E
					locMin.RightBound.Side = ClipperLib.EdgeSide.esRight
					locMin.RightBound.WindDelta = 0
					while true do
						if E.Bot.x ~= E.Prev.Top.x then
							self:ReverseHorizontal(E)
						end
						if E.Next.OutIdx == ClipperLib.ClipperBase.Skip then
							break
						end
						E.NextInLML = E.Next
						E = E.Next
					end
					self:InsertLocalMinima(locMin)
					table.insert(self.m_edges, edges)
					return true
				end
				table.insert(self.m_edges, edges)
				local leftBoundIsForward = nil
				local EMin = nil
				if ClipperLib.Point.op_Equality(E.Prev.Bot, E.Prev.Top) then
					E = E.Next
				end
				while true do
					E = self:FindNextLocMin(E)
					if E == EMin then
						break
					elseif EMin == nil then
						EMin = E
					end
					local locMin = LocalMinima()
					locMin.Next = nil
					locMin.y = E.Bot.y
					if E.Dx < E.Prev.Dx then
						locMin.LeftBound = E.Prev
						locMin.RightBound = E
						leftBoundIsForward = false
					else
						locMin.LeftBound = E
						locMin.RightBound = E.Prev
						leftBoundIsForward = true
					end
					locMin.LeftBound.Side = ClipperLib.EdgeSide.esLeft
					locMin.RightBound.Side = ClipperLib.EdgeSide.esRight
					if not Closed then
						locMin.LeftBound.WindDelta = 0
					elseif locMin.LeftBound.Next == locMin.RightBound then
						locMin.LeftBound.WindDelta = -1
					else
						locMin.LeftBound.WindDelta = 1
					end
					locMin.RightBound.WindDelta = -locMin.LeftBound.WindDelta
					E = self:ProcessBound(locMin.LeftBound, leftBoundIsForward)
					if E.OutIdx == ClipperLib.ClipperBase.Skip then
						E = self:ProcessBound(E, leftBoundIsForward)
					end
					local E2 = self:ProcessBound(locMin.RightBound, not leftBoundIsForward)
					if E2.OutIdx == ClipperLib.ClipperBase.Skip then
						E2 = self:ProcessBound(E2, not leftBoundIsForward)
					end
					if locMin.LeftBound.OutIdx == ClipperLib.ClipperBase.Skip then
						locMin.LeftBound = nil
					elseif locMin.RightBound.OutIdx == ClipperLib.ClipperBase.Skip then
						locMin.RightBound = nil
					end
					self:InsertLocalMinima(locMin)
					if not leftBoundIsForward then
						E = E2
					end
				end
				return true
			end,

			AddPaths = function(self, ppg, polyType, closed)
				local result = false
				for i = 1, #ppg do
					if self:AddPath(ppg[i], polyType, closed) then
						result = true
					end
				end
				return result
			end,

			Pt2IsBetweenPt1AndPt3 = function(self, pt1, pt2, pt3)
				if ((ClipperLib.Point.op_Equality(pt1, pt3)) or (ClipperLib.Point.op_Equality(pt1, pt2)) or
					(ClipperLib.Point.op_Equality(pt3, pt2))) then
					return false
				elseif pt1.x ~= pt3.x then
					return (pt2.x > pt1.x) == (pt2.x < pt3.x)
				else
					return (pt2.y > pt1.y) == (pt2.y < pt3.y)
				end
			end,

			RemoveEdge = function(self, e)
				e.Prev.Next = e.Next
				e.Next.Prev = e.Prev
				local result = e.Next
				e.Prev = nil
				return result
			end,

			SetDx = function(self, e)
				e.Delta.x = e.Top.x - e.Bot.x
				e.Delta.y = e.Top.y - e.Bot.y
				if e.Delta.y == 0 then
					e.Dx = ClipperLib.ClipperBase.horizontal
				else
					e.Dx = e.Delta.x / e.Delta.y
				end
			end,

			InsertLocalMinima = function(self, newLm)
				if self.m_MinimaList == nil then
					self.m_MinimaList = newLm
				elseif newLm.y >= self.m_MinimaList.y then
					newLm.Next = self.m_MinimaList
					self.m_MinimaList = newLm
				else
					local tmpLm = self.m_MinimaList
					while tmpLm.Next ~= nil and newLm.y < tmpLm.Next.y do
						tmpLm = tmpLm.Next
					end
					newLm.Next = tmpLm.Next
					tmpLm.Next = newLm
				end
			end,

			PopLocalMinima = function(self, Y, current)
				current.v = self.m_CurrentLM
				if self.m_CurrentLM ~= nil and self.m_CurrentLM.y == Y then
					self.m_CurrentLM = self.m_CurrentLM.Next
					return true
				end
				return false
			end,

			ReverseHorizontal = function(self, e)
				local tmp = e.Top.x
				e.Top.x = e.Bot.x
				e.Bot.x = tmp
			end,

			Reset = function(self)
				self.m_CurrentLM = self.m_MinimaList
				if self.m_CurrentLM == nil then
					return
				end
				self.m_Scanbeam = nil
				local lm = self.m_MinimaList
				while lm ~= nil do
					self:InsertScanbeam(lm.y)
					local e = lm.LeftBound
					if e ~= nil then
						e.Curr.x = e.Bot.x
						e.Curr.y = e.Bot.y
						e.OutIdx = ClipperLib.ClipperBase.Unassigned
					end
					e = lm.RightBound
					if e ~= nil then
						e.Curr.x = e.Bot.x
						e.Curr.y = e.Bot.y
						e.OutIdx = ClipperLib.ClipperBase.Unassigned
					end
					lm = lm.Next
				end
				self.m_ActiveEdges = nil
			end,

			InsertScanbeam = function(self, Y)
				if self.m_Scanbeam == nil then
					self.m_Scanbeam = Scanbeam()
					self.m_Scanbeam.Next = nil
					self.m_Scanbeam.y = Y
				elseif Y > self.m_Scanbeam.y then
					local newSb = Scanbeam()
					newSb.y = Y
					newSb.Next = self.m_Scanbeam
					self.m_Scanbeam = newSb
				else
					local sb2 = self.m_Scanbeam
					while sb2.Next ~= nil and Y <= sb2.Next.y do
						sb2 = sb2.Next
					end
					if Y == sb2.y then
						return
					end
					local newSb1 = Scanbeam()
					newSb1.y = Y
					newSb1.Next = sb2.Next
					sb2.Next = newSb1
				end
			end,

			PopScanbeam = function(self, Y)
				if self.m_Scanbeam == nil then
					Y.v = 0
					return false
				end
				Y.v = self.m_Scanbeam.y
				self.m_Scanbeam = self.m_Scanbeam.Next
				return true
			end,

			LocalMinimaPending = function(self)
				return self.m_CurrentLM ~= nil
			end,

			CreateOutRec = function(self)
				local result = OutRec()
				result.Idx = ClipperLib.ClipperBase.Unassigned
				result.IsHole = false
				result.IsOpen = false
				result.FirstLeft = nil
				result.Pts = nil
				result.BottomPt = nil
				result.PolyNode = nil
				table.insert(self.m_PolyOuts, result)
				result.Idx = #self.m_PolyOuts
				return result
			end,

			DisposeOutRec = function(self, index)
				local outRec = self.m_PolyOuts[index]
				outRec.Pts = nil
				outRec = nil
				self.m_PolyOuts[index] = nil
			end,

			UpdateEdgeIntoAEL = function(self, e)
				if e.NextInLML == nil then
					ClipperLib.Error("UpdateEdgeIntoAEL: invalid call")
				end
				local AelPrev = e.PrevInAEL
				local AelNext = e.NextInAEL
				e.NextInLML.OutIdx = e.OutIdx
				if AelPrev ~= nil then
					AelPrev.NextInAEL = e.NextInLML
				else
					self.m_ActiveEdges = e.NextInLML
				end
				if AelNext ~= nil then
					AelNext.PrevInAEL = e.NextInLML
				end
				e.NextInLML.Side = e.Side
				e.NextInLML.WindDelta = e.WindDelta
				e.NextInLML.WindCnt = e.WindCnt
				e.NextInLML.WindCnt2 = e.WindCnt2
				e = e.NextInLML
				e.Curr.x = e.Bot.x
				e.Curr.y = e.Bot.y
				e.PrevInAEL = AelPrev
				e.NextInAEL = AelNext
				if not ClipperLib.ClipperBase.IsHorizontal(e) then
					self:InsertScanbeam(e.Top.y)
				end
				return e
			end,

			SwapPositionsInAEL = function(self, edge1, edge2)
				if edge1.NextInAEL == edge1.PrevInAEL or edge2.NextInAEL == edge2.PrevInAEL then
					return
				end
				if edge1.NextInAEL == edge2 then
					local next = edge2.NextInAEL
					if next ~= nil then
						next.PrevInAEL = edge1
					end
					local prev = edge1.PrevInAEL
					if prev ~= nil then
						prev.NextInAEL = edge2
					end
					edge2.PrevInAEL = prev
					edge2.NextInAEL = edge1
					edge1.PrevInAEL = edge2
					edge1.NextInAEL = next
				elseif edge2.NextInAEL == edge1 then
					local next1 = edge1.NextInAEL
					if next1 ~= nil then
						next1.PrevInAEL = edge2
					end
					local prev1 = edge2.PrevInAEL
					if prev1 ~= nil then
						prev1.NextInAEL = edge1
					end
					edge1.PrevInAEL = prev1
					edge1.NextInAEL = edge2
					edge2.PrevInAEL = edge1
					edge2.NextInAEL = next1
				else
					local next2 = edge1.NextInAEL
					local prev2 = edge1.PrevInAEL
					edge1.NextInAEL = edge2.NextInAEL
					if edge1.NextInAEL ~= nil then
						edge1.NextInAEL.PrevInAEL = edge1
					end
					edge1.PrevInAEL = edge2.PrevInAEL
					if edge1.PrevInAEL ~= nil then
						edge1.PrevInAEL.NextInAEL = edge1
					end
					edge2.NextInAEL = next2
					if edge2.NextInAEL ~= nil then
						edge2.NextInAEL.PrevInAEL = edge2
					end
					edge2.PrevInAEL = prev2
					if edge2.PrevInAEL ~= nil then
						edge2.PrevInAEL.NextInAEL = edge2
					end
				end
				if edge1.PrevInAEL == nil then
					self.m_ActiveEdges = edge1
				else
					if edge2.PrevInAEL == nil then
						self.m_ActiveEdges = edge2
					end
				end
			end,

			DeleteFromAEL = function(self, e)
				local AelPrev = e.PrevInAEL
				local AelNext = e.NextInAEL
				if AelPrev == nil and AelNext == nil and e ~= self.m_ActiveEdges then
					return
				end
				if AelPrev ~= nil then
					AelPrev.NextInAEL = AelNext
				else
					self.m_ActiveEdges = AelNext
				end
				if AelNext ~= nil then
					AelNext.PrevInAEL = AelPrev
				end
				e.NextInAEL = nil
				e.PrevInAEL = nil
			end
		}
	)

	--CLASS CLIPPER
	local Clipper = class.extends(ClipperBase, "Clipper",
		function(self, InitOptions)
			if InitOptions == nil then
				InitOptions = 0
			end
			self.m_edges = {}
			self.m_ClipType = ClipperLib.ClipType.ctIntersection
			self.m_ClipFillType = ClipperLib.PolyFillType.pftEvenOdd
			self.m_SubjFillType = ClipperLib.PolyFillType.pftEvenOdd
			self.m_Scanbeam = nil
			self.m_Maxima = nil
			self.m_ActiveEdges = nil
			self.m_SortedEdges = nil
			self.m_IntersectList = {}
			self.m_IntersectNodeComparer = ClipperLib.MyIntersectNodeSort.Compare
			self.m_ExecuteLocked = false
			self.m_PolyOuts = {}
			self.m_Joins = {}
			self.m_GhostJoins = {}
			self.ReverseSolution = false
			self.StrictlySimple = false
			--self.PreserveCollinear = false
			self.FinalSolution = nil
		end,
		{
			Clear = function(self)
				if #self.m_edges == 0 then
					return
				end
				return self:DisposeAllPolyPts()
			end,

			InsertMaxima = function(self, X)
				local newMax = Maxima()
				newMax.x = X
				if self.m_Maxima == nil then
					self.m_Maxima = newMax
					self.m_Maxima.Next = nil
					self.m_Maxima.Prev = nil
				elseif X < self.m_Maxima.x then
					newMax.Next = self.m_Maxima
					newMax.Prev = nil
					self.m_Maxima = newMax
				else
					local m = self.m_Maxima
					while m.Next ~= nil and X >= m.Next.x do
						m = m.Next
					end
					if X == m.x then
						return
					end
					newMax.Next = m.Next
					newMax.Prev = m
					if m.Next ~= nil then
						m.Next.Prev = newMax
					end
					m.Next = newMax
				end
			end,

			Execute = function(self, clipType, subjFillType, clipFillType)
				self.m_ExecuteLocked = true
				self.m_SubjFillType = subjFillType
				self.m_ClipFillType = clipFillType
				self.m_ClipType = clipType
				local succeeded = self:ExecuteInternal()
				if succeeded then
					self:BuildResult()
				end
				self:DisposeAllPolyPts()
				self.m_ExecuteLocked = false
			end,

			FixHoleLinkage = function(self, outRec)
				if (outRec.FirstLeft == nil or (outRec.IsHole ~= outRec.FirstLeft.IsHole and outRec.FirstLeft.Pts ~= nil)) then
					return
				end
				local orfl = outRec.FirstLeft
				while (orfl ~= nil and ((orfl.IsHole == outRec.IsHole) or orfl.Pts == nil)) do
					orfl = orfl.FirstLeft
				end
				outRec.FirstLeft = orfl
			end,

			ExecuteInternal = function(self)
				self:Reset()
				self.m_SortedEdges = nil
				self.m_Maxima = nil
				local botY = {}
				local topY = {}
				if not self:PopScanbeam(botY) then
					return false
				end
				self:InsertLocalMinimaIntoAEL(botY.v)
				while self:PopScanbeam(topY) or self:LocalMinimaPending() do
					self:ProcessHorizontals()
					self.m_GhostJoins = {}
					if not self:ProcessIntersections(topY.v) then
						return false
					end
					self:ProcessEdgesAtTopOfScanbeam(topY.v)
					botY.v = topY.v
					self:InsertLocalMinimaIntoAEL(botY.v)
				end
				local outRec = nil
				for i = 1, #self.m_PolyOuts do
					outRec = self.m_PolyOuts[i]
					if outRec.Pts == nil or outRec.IsOpen then
						goto continue
					end
					if (BitXOR(outRec.IsHole == true and 1 or 0, self.ReverseSolution == true and 1 or 0)) == ((self:AreaS1(outRec) > 0) == true and 1 or 0) then
						self:ReversePolyPtLinks(outRec.Pts)
					end
					::continue::
				end
				self:JoinCommonEdges()
				for i = 1, #self.m_PolyOuts do
					outRec = self.m_PolyOuts[i]
					if outRec.Pts == nil then
						goto continue
					elseif outRec.IsOpen then
						self:FixupOutPolyline(outRec)
					else
						self:FixupOutPolygon(outRec)
					end
					::continue::
				end
				if self.StrictlySimple then
					self:DoSimplePolygons()
				end
				self.m_Joins = {}
				self.m_GhostJoins = {}
				return true
			end,

			DisposeAllPolyPts = function(self)
				for i = 1, #self.m_PolyOuts do
					self:DisposeOutRec(i)
				end
				self.m_PolyOuts = ClipperLib.Clear()
			end,

			AddJoin = function(self, Op1, Op2, OffPt)
				local j = Join()
				j.OutPt1 = Op1
				j.OutPt2 = Op2
				j.OffPt.x = OffPt.x
				j.OffPt.y = OffPt.y
				return table.insert(self.m_Joins, j)
			end,

			AddGhostJoin = function(self, Op, OffPt)
				local j = Join()
				j.OutPt1 = Op
				j.OffPt.x = OffPt.x
				j.OffPt.y = OffPt.y
				return table.insert(self.m_GhostJoins, j)
			end,

			InsertLocalMinimaIntoAEL = function(self, botY)
				local lm = {}
				local lb = nil
				local rb = nil
				while self:PopLocalMinima(botY, lm) do
					lb = lm.v.LeftBound
					rb = lm.v.RightBound
					local Op1 = nil
					if lb == nil then
						self:InsertEdgeIntoAEL(rb, nil)
						self:SetWindingCount(rb)
						if self:IsContributing(rb) then
							Op1 = self:AddOutPt(rb, rb.Bot)
						end
					elseif rb == nil then
						self:InsertEdgeIntoAEL(lb, nil)
						self:SetWindingCount(lb)
						if self:IsContributing(lb) then
							Op1 = self:AddOutPt(lb, lb.Bot)
						end
						self:InsertScanbeam(lb.Top.y)
					else
						self:InsertEdgeIntoAEL(lb, nil)
						self:InsertEdgeIntoAEL(rb, lb)
						self:SetWindingCount(lb)
						rb.WindCnt = lb.WindCnt
						rb.WindCnt2 = lb.WindCnt2
						if self:IsContributing(lb) then
							Op1 = self:AddLocalMinPoly(lb, rb, lb.Bot)
						end
						self:InsertScanbeam(lb.Top.y)
					end
					if rb ~= nil then
						if ClipperLib.ClipperBase.IsHorizontal(rb) then
							if rb.NextInLML ~= nil then
								self:InsertScanbeam(rb.NextInLML.Top.y)
							end
							self:AddEdgeToSEL(rb)
						else
							self:InsertScanbeam(rb.Top.y)
						end
					end
					if lb == nil or rb == nil then
						goto continue
					end
					if (Op1 ~= nil and ClipperLib.ClipperBase.IsHorizontal(rb) and #self.m_GhostJoins > 0 and rb.WindDelta ~= 0) then
						for i = 1, #self.m_GhostJoins do
							local j = self.m_GhostJoins[i]
							if self:HorzSegmentsOverlap(j.OutPt1.Pt.x, j.OffPt.x, rb.Bot.x, rb.Top.x) then
								self:AddJoin(j.OutPt1, Op1, j.OffPt)
							end
						end
					end
					if (lb.OutIdx >= 0 and lb.PrevInAEL ~= nil and lb.PrevInAEL.Curr.x == lb.Bot.x and
						lb.PrevInAEL.OutIdx >= 0 and
						ClipperLib.ClipperBase.SlopesEqual(lb.PrevInAEL.Curr, lb.PrevInAEL.Top, lb.Curr, lb.Top) and
						lb.WindDelta ~= 0 and lb.PrevInAEL.WindDelta ~= 0) then
						local Op2 = self:AddOutPt(lb.PrevInAEL, lb.Bot)
						self:AddJoin(Op1, Op2, lb.Top)
					end
					if lb.NextInAEL ~= rb then
						if (rb.OutIdx >= 0 and rb.PrevInAEL.OutIdx >= 0 and
							ClipperLib.ClipperBase.SlopesEqual(rb.PrevInAEL.Curr, rb.PrevInAEL.Top, rb.Curr, rb.Top) and
							rb.WindDelta ~= 0 and rb.PrevInAEL.WindDelta ~= 0) then
							local Op2 = self:AddOutPt(rb.PrevInAEL, rb.Bot)
							self:AddJoin(Op1, Op2, rb.Top)
						end
						local e = lb.NextInAEL
						if e ~= nil then
							while e ~= rb do
								self:IntersectEdges(rb, e, lb.Curr)
								e = e.NextInAEL
							end
						end
					end
					::continue::
				end
			end,

			InsertEdgeIntoAEL = function(self, edge, startEdge)
				if self.m_ActiveEdges == nil then
					edge.PrevInAEL = nil
					edge.NextInAEL = nil
					self.m_ActiveEdges = edge
				elseif startEdge == nil and self:E2InsertsBeforeE1(self.m_ActiveEdges, edge) then
					edge.PrevInAEL = nil
					edge.NextInAEL = self.m_ActiveEdges
					self.m_ActiveEdges.PrevInAEL = edge
					self.m_ActiveEdges = edge
				else
					if startEdge == nil then
						startEdge = self.m_ActiveEdges
					end
					while startEdge.NextInAEL ~= nil and not self:E2InsertsBeforeE1(startEdge.NextInAEL, edge) do
						startEdge = startEdge.NextInAEL
					end
					edge.NextInAEL = startEdge.NextInAEL
					if startEdge.NextInAEL ~= nil then
						startEdge.NextInAEL.PrevInAEL = edge
					end
					edge.PrevInAEL = startEdge
					startEdge.NextInAEL = edge
				end
			end,

			E2InsertsBeforeE1 = function(self, e1, e2)
				if e2.Curr.x == e1.Curr.x then
					if e2.Top.y > e1.Top.y then
						return e2.Top.x < ClipperLib.Clipper.TopX(e1, e2.Top.y)
					else
						return e1.Top.x > ClipperLib.Clipper.TopX(e2, e1.Top.y)
					end
				else
					return e2.Curr.x < e1.Curr.x
				end
			end,

			IsEvenOddFillType = function(self, edge)
				if edge.PolyTyp == ClipperLib.PolyType.ptSubject then
					return self.m_SubjFillType == ClipperLib.PolyFillType.pftEvenOdd
				else
					return self.m_ClipFillType == ClipperLib.PolyFillType.pftEvenOdd
				end
			end,

			IsEvenOddAltFillType = function(self, edge)
				if edge.PolyTyp == ClipperLib.PolyType.ptSubject then
					return self.m_ClipFillType == ClipperLib.PolyFillType.pftEvenOdd
				else
					return self.m_SubjFillType == ClipperLib.PolyFillType.pftEvenOdd
				end
			end,

			IsContributing = function(self, edge)
				local pft = nil
				local pft2 = nil
				if edge.PolyTyp == ClipperLib.PolyType.ptSubject then
					pft = self.m_SubjFillType
					pft2 = self.m_ClipFillType
				else
					pft = self.m_ClipFillType
					pft2 = self.m_SubjFillType
				end
				if ClipperLib.PolyFillType.pftEvenOdd == pft then
					if edge.WindDelta == 0 and edge.WindCnt ~= 1 then
						return false
					end
				elseif ClipperLib.PolyFillType.pftNonZero == pft then
					if math.abs(edge.WindCnt) ~= 1 then
						return false
					end
				elseif ClipperLib.PolyFillType.pftPositive == pft then
					if edge.WindCnt ~= 1 then
						return false
					end
				else
					if edge.WindCnt ~= -1 then
						return false
					end
				end
				if ClipperLib.ClipType.ctIntersection == self.m_ClipType then
					if ClipperLib.PolyFillType.pftEvenOdd == pft2 then
						return edge.WindCnt2 ~= 0
					elseif ClipperLib.PolyFillType.pftNonZero == pft2 then
						return edge.WindCnt2 ~= 0
					elseif ClipperLib.PolyFillType.pftPositive == pft2 then
						return edge.WindCnt2 > 0
					else
						return edge.WindCnt2 < 0
					end
				elseif ClipperLib.ClipType.ctUnion == self.m_ClipType then
					if ClipperLib.PolyFillType.pftEvenOdd == pft2 then
						return edge.WindCnt2 == 0
					elseif ClipperLib.PolyFillType.pftNonZero == pft2 then
						return edge.WindCnt2 == 0
					elseif ClipperLib.PolyFillType.pftPositive == pft2 then
						return edge.WindCnt2 <= 0
					else
						return edge.WindCnt2 >= 0
					end
				elseif ClipperLib.ClipType.ctDifference == self.m_ClipType then
					if edge.PolyTyp == ClipperLib.PolyType.ptSubject then
						if ClipperLib.PolyFillType.pftEvenOdd == pft2 then
							return edge.WindCnt2 == 0
						elseif ClipperLib.PolyFillType.pftNonZero == pft2 then
							return edge.WindCnt2 == 0
						elseif ClipperLib.PolyFillType.pftPositive == pft2 then
							return edge.WindCnt2 <= 0
						else
							return edge.WindCnt2 >= 0
						end
					else
						if ClipperLib.PolyFillType.pftEvenOdd == pft2 then
							return edge.WindCnt2 ~= 0
						elseif ClipperLib.PolyFillType.pftNonZero == pft2 then
							return edge.WindCnt2 ~= 0
						elseif ClipperLib.PolyFillType.pftPositive == pft2 then
							return edge.WindCnt2 > 0
						else
							return edge.WindCnt2 < 0
						end
					end
				elseif ClipperLib.ClipType.ctXor == self.m_ClipType then
					if edge.WindDelta == 0 then
						if ClipperLib.PolyFillType.pftEvenOdd == pft2 then
							return edge.WindCnt2 == 0
						elseif ClipperLib.PolyFillType.pftNonZero == pft2 then
							return edge.WindCnt2 == 0
						elseif ClipperLib.PolyFillType.pftPositive == pft2 then
							return edge.WindCnt2 <= 0
						else
							return edge.WindCnt2 >= 0
						end
					else
						return true
					end
				end
				return true
			end,

			SetWindingCount = function(self, edge)
				local e = edge.PrevInAEL
				while e ~= nil and (e.PolyTyp ~= edge.PolyTyp or e.WindDelta == 0) do
					e = e.PrevInAEL
				end
				if e == nil then
					local pft = nil
					if edge.PolyTyp == ClipperLib.PolyType.ptSubject then
						pft = self.m_SubjFillType
					else
						pft = self.m_ClipFillType
					end
					if edge.WindDelta == 0 then
						edge.WindCnt = nil
						if pft == ClipperLib.PolyFillType.pftNegative then
							edge.WindCnt = -1
						else
							edge.WindCnt = 1
						end
					else
						edge.WindCnt = edge.WindDelta
					end
					edge.WindCnt2 = 0
					e = self.m_ActiveEdges
				elseif edge.WindDelta == 0 and self.m_ClipType ~= ClipperLib.ClipType.ctUnion then
					edge.WindCnt = 1
					edge.WindCnt2 = e.WindCnt2
					e = e.NextInAEL
				elseif self:IsEvenOddFillType(edge) then
					if edge.WindDelta == 0 then
						local Inside = true
						local e2 = e.PrevInAEL
						while e2 ~= nil do
							if e2.PolyTyp == e.PolyTyp and e2.WindDelta ~= 0 then
								Inside = not Inside
							end
							e2 = e2.PrevInAEL
						end
						edge.WindCnt = nil
						if Inside then
							edge.WindCnt = 0
						else
							edge.WindCnt = 1
						end
					else
						edge.WindCnt = edge.WindDelta
					end
					edge.WindCnt2 = e.WindCnt2
					e = e.NextInAEL
				else
					if e.WindCnt * e.WindDelta < 0 then
						if math.abs(e.WindCnt) > 1 then
							if e.WindDelta * edge.WindDelta < 0 then
								edge.WindCnt = e.WindCnt
							else
								edge.WindCnt = e.WindCnt + edge.WindDelta
							end
						else
							edge.WindCnt = nil
							if edge.WindDelta == 0 then
								edge.WindCnt = 1
							else
								edge.WindCnt = edge.WindDelta
							end
						end
					else
						if edge.WindDelta == 0 then
							edge.WindCnt = nil
							if e.WindCnt < 0 then
								edge.WindCnt = e.WindCnt - 1
							else
								edge.WindCnt = e.WindCnt + 1
							end
						else
							if e.WindDelta * edge.WindDelta < 0 then
								edge.WindCnt = e.WindCnt
							else
								edge.WindCnt = e.WindCnt + edge.WindDelta
							end
						end
					end
					edge.WindCnt2 = e.WindCnt2
					e = e.NextInAEL
				end
				if self:IsEvenOddAltFillType(edge) then
					while e ~= edge do
						if e.WindDelta ~= 0 then
							edge.TempWindCnt2 = nil
							if edge.WindCnt2 == 0 then
								edge.TempWindCnt2 = 1
							else
								edge.TempWindCnt2 = 0
							end
							edge.WindCnt2 = edge.TempWindCnt2
						end
						e = e.NextInAEL
					end
				else
					while e ~= edge do
						edge.WindCnt2 = edge.WindCnt2 + e.WindDelta
						e = e.NextInAEL
					end
				end
			end,

			AddEdgeToSEL = function(self, edge)
				if self.m_SortedEdges == nil then
					self.m_SortedEdges = edge
					edge.PrevInSEL = nil
					edge.NextInSEL = nil
				else
					edge.NextInSEL = self.m_SortedEdges
					edge.PrevInSEL = nil
					self.m_SortedEdges.PrevInSEL = edge
					self.m_SortedEdges = edge
				end
			end,

			PopEdgeFromSEL = function(self, e)
				e.v = self.m_SortedEdges
				if e.v == nil then
					return false
				end
				local oldE = e.v
				self.m_SortedEdges = e.v.NextInSEL
				if self.m_SortedEdges ~= nil then
					self.m_SortedEdges.PrevInSEL = nil
				end
				oldE.NextInSEL = nil
				oldE.PrevInSEL = nil
				return true
			end,

			CopyAELToSEL = function(self)
				local e = self.m_ActiveEdges
				self.m_SortedEdges = e
				while e ~= nil do
					e.PrevInSEL = e.PrevInAEL
					e.NextInSEL = e.NextInAEL
					e = e.NextInAEL
				end
			end,

			SwapPositionsInSEL = function(self, edge1, edge2)
				if edge1.NextInSEL == nil and edge1.PrevInSEL == nil then
					return
				end
				if edge2.NextInSEL == nil and edge2.PrevInSEL == nil then
					return
				end
				if edge1.NextInSEL == edge2 then
					local next = edge2.NextInSEL
					if next ~= nil then
						next.PrevInSEL = edge1
					end
					local prev = edge1.PrevInSEL
					if prev ~= nil then
						prev.NextInSEL = edge2
					end
					edge2.PrevInSEL = prev
					edge2.NextInSEL = edge1
					edge1.PrevInSEL = edge2
					edge1.NextInSEL = next
				elseif edge2.NextInSEL == edge1 then
					local next = edge1.NextInSEL
					if next ~= nil then
						next.PrevInSEL = edge2
					end
					local prev = edge2.PrevInSEL
					if prev ~= nil then
						prev.NextInSEL = edge1
					end
					edge1.PrevInSEL = prev
					edge1.NextInSEL = edge2
					edge2.PrevInSEL = edge1
					edge2.NextInSEL = next
				else
					local next = edge1.NextInSEL
					local prev = edge1.PrevInSEL
					edge1.NextInSEL = edge2.NextInSEL
					if edge1.NextInSEL ~= nil then
						edge1.NextInSEL.PrevInSEL = edge1
					end
					edge1.PrevInSEL = edge2.PrevInSEL
					if edge1.PrevInSEL ~= nil then
						edge1.PrevInSEL.NextInSEL = edge1
					end
					edge2.NextInSEL = next
					if edge2.NextInSEL ~= nil then
						edge2.NextInSEL.PrevInSEL = edge2
					end
					edge2.PrevInSEL = prev
					if edge2.PrevInSEL ~= nil then
						edge2.PrevInSEL.NextInSEL = edge2
					end
				end
				if edge1.PrevInSEL == nil then
					self.m_SortedEdges = edge1
				elseif edge2.PrevInSEL == nil then
					self.m_SortedEdges = edge2
				end
			end,

			AddLocalMaxPoly = function(self, e1, e2, pt)
				self:AddOutPt(e1, pt)
				if e2.WindDelta == 0 then
					self:AddOutPt(e2, pt)
				end
				if e1.OutIdx == e2.OutIdx then
					e1.OutIdx, e2.OutIdx = -1, -1
				elseif e1.OutIdx < e2.OutIdx then
					return self:AppendPolygon(e1, e2)
				else
					return self:AppendPolygon(e2, e1)
				end
			end,

			AddLocalMinPoly = function(self, e1, e2, pt)
				local result = nil
				local e = nil
				local prevE = nil
				if ClipperLib.ClipperBase.IsHorizontal(e2) or e1.Dx > e2.Dx then
					result = self:AddOutPt(e1, pt)
					e2.OutIdx = e1.OutIdx
					e1.Side = ClipperLib.EdgeSide.esLeft
					e2.Side = ClipperLib.EdgeSide.esRight
					e = e1
					if e.PrevInAEL == e2 then
						prevE = e2.PrevInAEL
					else
						prevE = e.PrevInAEL
					end
				else
					result = self:AddOutPt(e2, pt)
					e1.OutIdx = e2.OutIdx
					e1.Side = ClipperLib.EdgeSide.esRight
					e2.Side = ClipperLib.EdgeSide.esLeft
					e = e2
					if e.PrevInAEL == e1 then
						prevE = e1.PrevInAEL
					else
						prevE = e.PrevInAEL
					end
				end
				if prevE ~= nil and prevE.OutIdx >= 0 and prevE.Top.y < pt.y and e.Top.y < pt.y then
					local xPrev = ClipperLib.Clipper.TopX(prevE, pt.y)
					local xE = ClipperLib.Clipper.TopX(e, pt.y)
					if ((xPrev == xE) and (e.WindDelta ~= 0) and (prevE.WindDelta ~= 0) and
						ClipperLib.ClipperBase.SlopesEqual(Point(xPrev, pt.y), prevE.Top, Point(xE, pt.y), e.Top)) then
						local outPt = self:AddOutPt(prevE, pt)
						self:AddJoin(result, outPt, e.Top)
					end
				end
				return result
			end,

			AddOutPt = function(self, e, pt)
				if e.OutIdx < 0 then
					local outRec = self:CreateOutRec()
					outRec.IsOpen = e.WindDelta == 0
					local newOp = OutPt()
					outRec.Pts = newOp
					newOp.Idx = outRec.Idx
					newOp.Pt.x = pt.x
					newOp.Pt.y = pt.y
					newOp.Next = newOp
					newOp.Prev = newOp
					if not outRec.IsOpen then
						self:SetHoleState(e, outRec)
					end
					e.OutIdx = outRec.Idx
					return newOp
				else
					local outRec = self.m_PolyOuts[e.OutIdx]
					local op = outRec.Pts
					local ToFront = e.Side == ClipperLib.EdgeSide.esLeft
					if ToFront and ClipperLib.Point.op_Equality(pt, op.Pt) then
						return op
					elseif not ToFront and ClipperLib.Point.op_Equality(pt, op.Prev.Pt) then
						return op.Prev
					end
					local newOp = OutPt()
					newOp.Idx = outRec.Idx
					newOp.Pt.x = pt.x
					newOp.Pt.y = pt.y
					newOp.Next = op
					newOp.Prev = op.Prev
					newOp.Prev.Next = newOp
					op.Prev = newOp
					if ToFront then
						outRec.Pts = newOp
					end
					return newOp
				end
			end,

			GetLastOutPt = function(self, e)
				local outRec = self.m_PolyOuts[e.OutIdx]
				if e.Side == ClipperLib.EdgeSide.esLeft then
					return outRec.Pts
				else
					return outRec.Pts.Prev
				end
			end,

			SwapPoints = function(self, pt1, pt2)
				local tmp = Point(pt1.Value)
				pt1.Value.x = pt2.Value.x
				pt1.Value.y = pt2.Value.y
				pt2.Value.x = tmp.x
				pt2.Value.y = tmp.y
			end,

			HorzSegmentsOverlap = function(self, seg1a, seg1b, seg2a, seg2b)
				local tmp = nil
				if seg1a > seg1b then
					tmp = seg1a
					seg1a = seg1b
					seg1b = tmp
				end
				if seg2a > seg2b then
					tmp = seg2a
					seg2a = seg2b
					seg2b = tmp
				end
				return seg1a < seg2b and seg2a < seg1b
			end,

			SetHoleState = function(self, e, outRec)
				local e2 = e.PrevInAEL
				local eTmp = nil
				while e2 ~= nil do
					if e2.OutIdx >= 0 and e2.WindDelta ~= 0 then
						if eTmp == nil then
							eTmp = e2
						elseif eTmp.OutIdx == e2.OutIdx then
							eTmp = nil
						end
					end
					e2 = e2.PrevInAEL
				end
				if eTmp == nil then
					outRec.FirstLeft = nil
					outRec.IsHole = false
				else
					outRec.FirstLeft = self.m_PolyOuts[eTmp.OutIdx]
					outRec.IsHole = not outRec.FirstLeft.IsHole
				end
			end,

			GetDx = function(self, pt1, pt2)
				if pt1.y == pt2.y then
					return ClipperLib.ClipperBase.horizontal
				else
					return (pt2.x - pt1.x) / (pt2.y - pt1.y)
				end
			end,

			FirstIsBottomPt = function(self, btmPt1, btmPt2)
				local p = btmPt1.Prev
				while ClipperLib.Point.op_Equality(p.Pt, btmPt1.Pt) and p ~= btmPt1 do
					p = p.Prev
				end
				local dx1p = math.abs(self:GetDx(btmPt1.Pt, p.Pt))
				p = btmPt1.Next
				while ClipperLib.Point.op_Equality(p.Pt, btmPt1.Pt) and p ~= btmPt1 do
					p = p.Next
				end
				local dx1n = math.abs(self:GetDx(btmPt1.Pt, p.Pt))
				p = btmPt2.Prev
				while ClipperLib.Point.op_Equality(p.Pt, btmPt2.Pt) and p ~= btmPt2 do
					p = p.Prev
				end
				local dx2p = math.abs(self:GetDx(btmPt2.Pt, p.Pt))
				p = btmPt2.Next
				while ClipperLib.Point.op_Equality(p.Pt, btmPt2.Pt) and p ~= btmPt2 do
					p = p.Next
				end
				local dx2n = math.abs(self:GetDx(btmPt2.Pt, p.Pt))
				if math.max(dx1p, dx1n) == math.max(dx2p, dx2n) and math.min(dx1p, dx1n) == math.min(dx2p, dx2n) then
					return self:Area(btmPt1) > 0
				else
					return (dx1p >= dx2p and dx1p >= dx2n) or (dx1n >= dx2p and dx1n >= dx2n)
				end
			end,

			GetBottomPt = function(self, pp)
				local dups = nil
				local p = pp.Next
				while p ~= pp do
					if p.Pt.y > pp.Pt.y then
						pp = p
						dups = nil
					else
						if p.Pt.y == pp.Pt.y and p.Pt.x <= pp.Pt.x then
							if p.Pt.x < pp.Pt.x then
								dups = nil
								pp = p
							else
								if p.Next ~= pp and p.Prev ~= pp then
									dups = p
								end
							end
						end
					end
					p = p.Next
				end
				if dups ~= nil then
					while dups ~= p do
						if not self:FirstIsBottomPt(p, dups) then
							pp = dups
						end
						dups = dups.Next
						while ClipperLib.Point.op_Inequality(dups.Pt, pp.Pt) do
							dups = dups.Next
						end
					end
				end
				return pp
			end,

			GetLowermostRec = function(self, outRec1, outRec2)
				if outRec1.BottomPt == nil then
					outRec1.BottomPt = self:GetBottomPt(outRec1.Pts)
				end
				if outRec2.BottomPt == nil then
					outRec2.BottomPt = self:GetBottomPt(outRec2.Pts)
				end
				local bPt1 = outRec1.BottomPt
				local bPt2 = outRec2.BottomPt
				if bPt1.Pt.y > bPt2.Pt.y then
					return outRec1
				elseif bPt1.Pt.y < bPt2.Pt.y then
					return outRec2
				elseif bPt1.Pt.x < bPt2.Pt.x then
					return outRec1
				elseif bPt1.Pt.x > bPt2.Pt.x then
					return outRec2
				elseif bPt1.Next == bPt1 then
					return outRec2
				elseif bPt2.Next == bPt2 then
					return outRec1
				elseif self:FirstIsBottomPt(bPt1, bPt2) then
					return outRec1
				else
					return outRec2
				end
			end,

			OutRec1RightOfOutRec2 = function(self, outRec1, outRec2)
				while true do
					outRec1 = outRec1.FirstLeft
					if outRec1 == outRec2 then
						return true
					end
					if outRec1 == nil then
						break
					end
				end
				return false
			end,

			GetOutRec = function(self, idx)
				local outrec = self.m_PolyOuts[idx]
				while outrec ~= self.m_PolyOuts[outrec.Idx] do
					outrec = self.m_PolyOuts[outrec.Idx]
				end
				return outrec
			end,

			AppendPolygon = function(self, e1, e2)
				local outRec1 = self.m_PolyOuts[e1.OutIdx]
				local outRec2 = self.m_PolyOuts[e2.OutIdx]
				local holeStateRec = nil
				if self:OutRec1RightOfOutRec2(outRec1, outRec2) then
					holeStateRec = outRec2
				elseif self:OutRec1RightOfOutRec2(outRec2, outRec1) then
					holeStateRec = outRec1
				else
					holeStateRec = self:GetLowermostRec(outRec1, outRec2)
				end
				local p1_lft = outRec1.Pts
				local p1_rt = p1_lft.Prev
				local p2_lft = outRec2.Pts
				local p2_rt = p2_lft.Prev
				if e1.Side == ClipperLib.EdgeSide.esLeft then
					if e2.Side == ClipperLib.EdgeSide.esLeft then
						self:ReversePolyPtLinks(p2_lft)
						p2_lft.Next = p1_lft
						p1_lft.Prev = p2_lft
						p1_rt.Next = p2_rt
						p2_rt.Prev = p1_rt
						outRec1.Pts = p2_rt
					else
						p2_rt.Next = p1_lft
						p1_lft.Prev = p2_rt
						p2_lft.Prev = p1_rt
						p1_rt.Next = p2_lft
						outRec1.Pts = p2_lft
					end
				else
					if e2.Side == ClipperLib.EdgeSide.esRight then
						self:ReversePolyPtLinks(p2_lft)
						p1_rt.Next = p2_rt
						p2_rt.Prev = p1_rt
						p2_lft.Next = p1_lft
						p1_lft.Prev = p2_lft
					else
						p1_rt.Next = p2_lft
						p2_lft.Prev = p1_rt
						p1_lft.Prev = p2_rt
						p2_rt.Next = p1_lft
					end
				end
				outRec1.BottomPt = nil
				if holeStateRec == outRec2 then
					if outRec2.FirstLeft ~= outRec1 then
						outRec1.FirstLeft = outRec2.FirstLeft
					end
					outRec1.IsHole = outRec2.IsHole
				end
				outRec2.Pts = nil
				outRec2.BottomPt = nil
				outRec2.FirstLeft = outRec1
				local OKIdx = e1.OutIdx
				local ObsoleteIdx = e2.OutIdx
				e1.OutIdx = -1
				e2.OutIdx = -1
				local e = self.m_ActiveEdges
				while e ~= nil do
					if e.OutIdx == ObsoleteIdx then
						e.OutIdx = OKIdx
						e.Side = e1.Side
						break
					end
					e = e.NextInAEL
				end
				outRec2.Idx = outRec1.Idx
			end,

			ReversePolyPtLinks = function(self, pp)
				if pp == nil then
					return
				end
				local pp1 = nil
				local pp2 = nil
				pp1 = pp
				while true do
					pp2 = pp1.Next
					pp1.Next = pp1.Prev
					pp1.Prev = pp2
					pp1 = pp2
					if pp1 == pp then
						break
					end
				end
			end,

			IntersectEdges = function(self, e1, e2, pt)
				local e1Contributing = e1.OutIdx >= 0
				local e2Contributing = e2.OutIdx >= 0
				if ClipperLib.use_lines then
					if e1.WindDelta == 0 or e2.WindDelta == 0 then
						if e1.WindDelta == 0 and e2.WindDelta == 0 then
							return
						elseif e1.PolyTyp == e2.PolyTyp and e1.WindDelta ~= e2.WindDelta and self.m_ClipType == ClipperLib.ClipType.ctUnion then
							if e1.WindDelta == 0 then
								if e2Contributing then
									self:AddOutPt(e1, pt)
									if e1Contributing then
										e1.OutIdx = -1
									end
								end
							else
								if e1Contributing then
									self:AddOutPt(e2, pt)
									if e2Contributing then
										e2.OutIdx = -1
									end
								end
							end
						elseif e1.PolyTyp ~= e2.PolyTyp then
							if (e1.WindDelta == 0 and math.abs(e2.WindCnt) == 1 and
								(self.m_ClipType ~= ClipperLib.ClipType.ctUnion or e2.WindCnt2 == 0)) then
								self:AddOutPt(e1, pt)
								if e1Contributing then
									e1.OutIdx = -1
								end
							else
								if (e2.WindDelta == 0 and math.abs(e1.WindCnt) == 1 and
									(self.m_ClipType ~= ClipperLib.ClipType.ctUnion or e1.WindCnt2 == 0)) then
									self:AddOutPt(e2, pt)
									if e2Contributing then
										e2.OutIdx = -1
									end
								end
							end
						end
						return
					end
				end
				if e1.PolyTyp == e2.PolyTyp then
					if self:IsEvenOddFillType(e1) then
						local oldE1WindCnt = e1.WindCnt
						e1.WindCnt = e2.WindCnt
						e2.WindCnt = oldE1WindCnt
					else
						if e1.WindCnt + e2.WindDelta == 0 then
							e1.WindCnt = -e1.WindCnt
						else
							e1.WindCnt = e1.WindCnt + e2.WindDelta
						end
						if e2.WindCnt - e1.WindDelta == 0 then
							e2.WindCnt = -e2.WindCnt
						else
							e2.WindCnt = e2.WindCnt - e1.WindDelta
						end
					end
				else
					if not self:IsEvenOddFillType(e2) then
						e1.WindCnt2 = e1.WindCnt2 + e2.WindDelta
					else
						e1.WindCnt2 = e1.WindCnt2 == 0 and 1 or 0
					end
					if not self:IsEvenOddFillType(e1) then
						e2.WindCnt2 = e2.WindCnt2 - e1.WindDelta
					else
						e2.WindCnt2 = e2.WindCnt2 == 0 and 1 or 0
					end
				end
				local e1FillType, e2FillType, e1FillType2, e2FillType2 = nil
				if e1.PolyTyp == ClipperLib.PolyType.ptSubject then
					e1FillType = self.m_SubjFillType
					e1FillType2 = self.m_ClipFillType
				else
					e1FillType = self.m_ClipFillType
					e1FillType2 = self.m_SubjFillType
				end
				if e2.PolyTyp == ClipperLib.PolyType.ptSubject then
					e2FillType = self.m_SubjFillType
					e2FillType2 = self.m_ClipFillType
				else
					e2FillType = self.m_ClipFillType
					e2FillType2 = self.m_SubjFillType
				end
				local e1Wc, e2Wc = nil
				if ClipperLib.PolyFillType.pftPositive == e1FillType then
					e1Wc = e1.WindCnt
				elseif ClipperLib.PolyFillType.pftNegative == e1FillType then
					e1Wc = -e1.WindCnt
				else
					e1Wc = math.abs(e1.WindCnt)
				end
				if ClipperLib.PolyFillType.pftPositive == e2FillType then
					e2Wc = e2.WindCnt
				elseif ClipperLib.PolyFillType.pftNegative == e2FillType then
					e2Wc = -e2.WindCnt
				else
					e2Wc = math.abs(e2.WindCnt)
				end
				if e1Contributing and e2Contributing then
					if ((e1Wc ~= 0 and e1Wc ~= 1) or (e2Wc ~= 0 and e2Wc ~= 1) or
						(e1.PolyTyp ~= e2.PolyTyp and self.m_ClipType ~= ClipperLib.ClipType.ctXor)) then
						return self:AddLocalMaxPoly(e1, e2, pt)
					else
						self:AddOutPt(e1, pt)
						self:AddOutPt(e2, pt)
						ClipperLib.Clipper.SwapSides(e1, e2)
						return ClipperLib.Clipper.SwapPolyIndexes(e1, e2)
					end
				elseif e1Contributing then
					if e2Wc == 0 or e2Wc == 1 then
						self:AddOutPt(e1, pt)
						ClipperLib.Clipper.SwapSides(e1, e2)
						return ClipperLib.Clipper.SwapPolyIndexes(e1, e2)
					end
				elseif e2Contributing then
					if e1Wc == 0 or e1Wc == 1 then
						self:AddOutPt(e2, pt)
						ClipperLib.Clipper.SwapSides(e1, e2)
						return ClipperLib.Clipper.SwapPolyIndexes(e1, e2)
					end
				elseif (e1Wc == 0 or e1Wc == 1) and (e2Wc == 0 or e2Wc == 1) then
					local e1Wc2, e2Wc2 = nil
					if ClipperLib.PolyFillType.pftPositive == e1FillType2 then
						e1Wc2 = e1.WindCnt2
					elseif ClipperLib.PolyFillType.pftNegative == e1FillType2 then
						e1Wc2 = -e1.WindCnt2
					else
						e1Wc2 = math.abs(e1.WindCnt2)
					end
					if ClipperLib.PolyFillType.pftPositive == e2FillType2 then
						e2Wc2 = e2.WindCnt2
					elseif ClipperLib.PolyFillType.pftNegative == e2FillType2 then
						e2Wc2 = -e2.WindCnt2
					else
						e2Wc2 = math.abs(e2.WindCnt2)
					end
					if e1.PolyTyp ~= e2.PolyTyp then
						return self:AddLocalMinPoly(e1, e2, pt)
					elseif e1Wc == 1 and e2Wc == 1 then
						if ClipperLib.ClipType.ctIntersection == self.m_ClipType then
							if e1Wc2 > 0 and e2Wc2 > 0 then
								return self:AddLocalMinPoly(e1, e2, pt)
							end
						elseif ClipperLib.ClipType.ctUnion == self.m_ClipType then
							if e1Wc2 <= 0 and e2Wc2 <= 0 then
								return self:AddLocalMinPoly(e1, e2, pt)
							end
						elseif ClipperLib.ClipType.ctDifference == self.m_ClipType then
							if (((e1.PolyTyp == ClipperLib.PolyType.ptClip) and (e1Wc2 > 0) and (e2Wc2 > 0)) or
								((e1.PolyTyp == ClipperLib.PolyType.ptSubject) and (e1Wc2 <= 0) and (e2Wc2 <= 0))) then
								return self:AddLocalMinPoly(e1, e2, pt)
							end
						elseif ClipperLib.ClipType.ctXor == self.m_ClipType then
							return self:AddLocalMinPoly(e1, e2, pt)
						end
					else
						return ClipperLib.Clipper.SwapSides(e1, e2)
					end
				end
			end,

			DeleteFromSEL = function(self, e)
				local SelPrev = e.PrevInSEL
				local SelNext = e.NextInSEL
				if (SelPrev == nil and SelNext == nil and (e ~= self.m_SortedEdges)) then
					return
				end
				if SelPrev ~= nil then
					SelPrev.NextInSEL = SelNext
				else
					self.m_SortedEdges = SelNext
				end
				if SelNext ~= nil then
					SelNext.PrevInSEL = SelPrev
				end
				e.NextInSEL = nil
				e.PrevInSEL = nil
			end,

			ProcessHorizontals = function(self)
				local horzEdge = {}
				while self:PopEdgeFromSEL(horzEdge) do
					self:ProcessHorizontal(horzEdge.v)
				end
			end,

			GetHorzDirection = function(self, HorzEdge, Svar)
				if HorzEdge.Bot.x < HorzEdge.Top.x then
					Svar.Left = HorzEdge.Bot.x
					Svar.Right = HorzEdge.Top.x
					Svar.Dir = ClipperLib.Direction.dLeftToRight
				else
					Svar.Left = HorzEdge.Top.x
					Svar.Right = HorzEdge.Bot.x
					Svar.Dir = ClipperLib.Direction.dRightToLeft
				end
			end,

			ProcessHorizontal = function(self, horzEdge)
				local Svar = {
					Dir = nil,
					Left = nil,
					Right = nil
				}
				self:GetHorzDirection(horzEdge, Svar)
				local dir = Svar.Dir
				local horzLeft = Svar.Left
				local horzRight = Svar.Right
				local IsOpen = horzEdge.WindDelta == 0
				local eLastHorz = horzEdge
				local eMaxPair = nil
				while (eLastHorz.NextInLML ~= nil and ClipperLib.ClipperBase.IsHorizontal(eLastHorz.NextInLML)) do
					eLastHorz = eLastHorz.NextInLML
				end
				if eLastHorz.NextInLML == nil then
					eMaxPair = self:GetMaximaPair(eLastHorz)
				end
				local currMax = self.m_Maxima
				if currMax ~= nil then
					if dir == ClipperLib.Direction.dLeftToRight then
						while currMax ~= nil and currMax.x <= horzEdge.Bot.x do
							currMax = currMax.Next
						end
						if currMax ~= nil and currMax.x >= eLastHorz.Top.x then
							currMax = nil
						end
					else
						while currMax.Next ~= nil and currMax.Next.x < horzEdge.Bot.x do
							currMax = currMax.Next
						end
						if currMax.x <= eLastHorz.Top.x then
							currMax = nil
						end
					end
				end
				local op1 = nil
				while true do
					local IsLastHorz = horzEdge == eLastHorz
					local e = self:GetNextInAEL(horzEdge, dir)
					while e ~= nil do
						if currMax ~= nil then
							if dir == ClipperLib.Direction.dLeftToRight then
								while currMax ~= nil and currMax.x < e.Curr.x do
									if horzEdge.OutIdx >= 0 and not IsOpen then
										self:AddOutPt(horzEdge, Point(currMax.x, horzEdge.Bot.y))
									end
									currMax = currMax.Next
								end
							else
								while currMax ~= nil and currMax.x > e.Curr.x do
									if horzEdge.OutIdx >= 0 and not IsOpen then
										self:AddOutPt(horzEdge, Point(currMax.x, horzEdge.Bot.y))
									end
									currMax = currMax.Prev
								end
							end
						end
						if ((dir == ClipperLib.Direction.dLeftToRight and e.Curr.x > horzRight) or
							(dir == ClipperLib.Direction.dRightToLeft and e.Curr.x < horzLeft)) then
							break
						end
						if e.Curr.x == horzEdge.Top.x and horzEdge.NextInLML ~= nil and e.Dx < horzEdge.NextInLML.Dx then
							break
						end
						if horzEdge.OutIdx >= 0 and not IsOpen then
							op1 = self:AddOutPt(horzEdge, e.Curr)
							local eNextHorz = self.m_SortedEdges
							while eNextHorz ~= nil do
								if (eNextHorz.OutIdx >= 0 and
									self:HorzSegmentsOverlap(horzEdge.Bot.x, horzEdge.Top.x, eNextHorz.Bot.x,
										eNextHorz.Top.x)) then
									local op2 = self:GetLastOutPt(eNextHorz)
									self:AddJoin(op2, op1, eNextHorz.Top)
								end
								eNextHorz = eNextHorz.NextInSEL
							end
							self:AddGhostJoin(op1, horzEdge.Bot)
						end
						if e == eMaxPair and IsLastHorz then
							if horzEdge.OutIdx >= 0 then
								self:AddLocalMaxPoly(horzEdge, eMaxPair, horzEdge.Top)
							end
							self:DeleteFromAEL(horzEdge)
							self:DeleteFromAEL(eMaxPair)
							return
						end
						if dir == ClipperLib.Direction.dLeftToRight then
							local Pt = Point(e.Curr.x, horzEdge.Curr.y)
							self:IntersectEdges(horzEdge, e, Pt)
						else
							local Pt = Point(e.Curr.x, horzEdge.Curr.y)
							self:IntersectEdges(e, horzEdge, Pt)
						end
						local eNext = self:GetNextInAEL(e, dir)
						self:SwapPositionsInAEL(horzEdge, e)
						e = eNext
					end
					if horzEdge.NextInLML == nil or not ClipperLib.ClipperBase.IsHorizontal(horzEdge.NextInLML) then
						break
					end
					horzEdge = self:UpdateEdgeIntoAEL(horzEdge)
					if horzEdge.OutIdx >= 0 then
						self:AddOutPt(horzEdge, horzEdge.Bot)
					end
					Svar = {
						Dir = dir,
						Left = horzLeft,
						Right = horzRight
					}
					self:GetHorzDirection(horzEdge, Svar)
					dir = Svar.Dir
					horzLeft = Svar.Left
					horzRight = Svar.Right
				end
				if horzEdge.OutIdx >= 0 and op1 == nil then
					op1 = self:GetLastOutPt(horzEdge)
					local eNextHorz = self.m_SortedEdges
					while eNextHorz ~= nil do
						if (eNextHorz.OutIdx >= 0 and
							self:HorzSegmentsOverlap(horzEdge.Bot.x, horzEdge.Top.x, eNextHorz.Bot.x, eNextHorz.Top.x)) then
							local op2 = self:GetLastOutPt(eNextHorz)
							self:AddJoin(op2, op1, eNextHorz.Top)
						end
						eNextHorz = eNextHorz.NextInSEL
					end
					self:AddGhostJoin(op1, horzEdge.Top)
				end
				if horzEdge.NextInLML ~= nil then
					if horzEdge.OutIdx >= 0 then
						op1 = self:AddOutPt(horzEdge, horzEdge.Top)
						horzEdge = self:UpdateEdgeIntoAEL(horzEdge)
						if horzEdge.WindDelta == 0 then
							return
						end
						local ePrev = horzEdge.PrevInAEL
						local eNext = horzEdge.NextInAEL
						if (ePrev ~= nil and ePrev.Curr.x == horzEdge.Bot.x and ePrev.Curr.y == horzEdge.Bot.y and
							ePrev.WindDelta == 0 and
							(ePrev.OutIdx >= 0 and ePrev.Curr.y > ePrev.Top.y and
								ClipperLib.ClipperBase.SlopesEqual(horzEdge, ePrev))) then
							local op2 = self:AddOutPt(ePrev, horzEdge.Bot)
							return self:AddJoin(op1, op2, horzEdge.Top)
						elseif (eNext ~= nil and eNext.Curr.x == horzEdge.Bot.x and eNext.Curr.y == horzEdge.Bot.y and
							eNext.WindDelta ~= 0 and eNext.OutIdx >= 0 and eNext.Curr.y > eNext.Top.y and
							ClipperLib.ClipperBase.SlopesEqual(horzEdge, eNext)) then
							local op2 = self:AddOutPt(eNext, horzEdge.Bot)
							return self:AddJoin(op1, op2, horzEdge.Top)
						end
					else
						horzEdge = self:UpdateEdgeIntoAEL(horzEdge)
					end
				else
					if horzEdge.OutIdx >= 0 then
						self:AddOutPt(horzEdge, horzEdge.Top)
					end
					return self:DeleteFromAEL(horzEdge)
				end
			end,

			GetNextInAEL = function(self, e, Direction)
				local r = nil
				if Direction == ClipperLib.Direction.dLeftToRight then
					r = e.NextInAEL
				else
					r = e.PrevInAEL
				end
				return r
			end,

			IsMinima = function(self, e)
				return e ~= nil and (e.Prev.NextInLML ~= e) and (e.Next.NextInLML ~= e)
			end,

			IsMaxima = function(self, e, Y)
				return (e ~= nil and e.Top.y == Y and e.NextInLML == nil)
			end,

			IsIntermediate = function(self, e, Y)
				return (e.Top.y == Y and e.NextInLML ~= nil)
			end,

			GetMaximaPair = function(self, e)
				if ((ClipperLib.Point.op_Equality(e.Next.Top, e.Top)) and e.Next.NextInLML == nil) then
					return e.Next
				else
					if ((ClipperLib.Point.op_Equality(e.Prev.Top, e.Top)) and e.Prev.NextInLML == nil) then
						return e.Prev
					else
						return nil
					end
				end
			end,

			GetMaximaPairEx = function(self, e)
				local result = self:GetMaximaPair(e)
				if (result == nil or result.OutIdx == ClipperLib.ClipperBase.Skip or
					((result.NextInAEL == result.PrevInAEL) and not ClipperLib.ClipperBase.IsHorizontal(result))) then
					return nil
				end
				return result
			end,

			ProcessIntersections = function(self, topY)
				if self.m_ActiveEdges == nil then
					return true
				end
				self:BuildIntersectList(topY)
				if #self.m_IntersectList == 0 then
					return true
				end
				if #self.m_IntersectList == 1 or self:FixupIntersectionOrder() then
					self:ProcessIntersectList()
				else
					return false
				end
				self.m_SortedEdges = nil
				return true
			end,

			BuildIntersectList = function(self, topY)
				if self.m_ActiveEdges == nil then
					return
				end
				local e = self.m_ActiveEdges
				self.m_SortedEdges = e
				while e ~= nil do
					e.PrevInSEL = e.PrevInAEL
					e.NextInSEL = e.NextInAEL
					e.Curr.x = ClipperLib.Clipper.TopX(e, topY)
					e = e.NextInAEL
				end
				local isModified = true
				while isModified and self.m_SortedEdges ~= nil do
					isModified = false
					e = self.m_SortedEdges
					while e.NextInSEL ~= nil do
						local eNext = e.NextInSEL
						local pt = Point()
						if e.Curr.x > eNext.Curr.x then
							self:IntersectPoint(e, eNext, pt)
							if pt.y < topY then
								pt = Point(ClipperLib.Clipper.TopX(e, topY), topY)
							end
							local newNode = IntersectNode()
							newNode.Edge1 = e
							newNode.Edge2 = eNext
							newNode.Pt.x = pt.x
							newNode.Pt.y = pt.y
							table.insert(self.m_IntersectList, newNode)
							self:SwapPositionsInSEL(e, eNext)
							isModified = true
						else
							e = eNext
						end
					end
					if e.PrevInSEL ~= nil then
						e.PrevInSEL.NextInSEL = nil
					else
						break
					end
				end
				self.m_SortedEdges = nil
			end,

			EdgesAdjacent = function(self, inode)
				return (inode.Edge1.NextInSEL == inode.Edge2) or (inode.Edge1.PrevInSEL == inode.Edge2)
			end,

			FixupIntersectionOrder = function(self)
				table.sort(self.m_IntersectList, self.m_IntersectNodeComparer)
				self:CopyAELToSEL()
				local cnt = #self.m_IntersectList
				for i = 1, cnt do
					if not self:EdgesAdjacent(self.m_IntersectList[i]) then
						local j = i + 1
						while j < cnt and not self:EdgesAdjacent(self.m_IntersectList[j]) do
							j = j + 1
						end
						if j == cnt then
							return false
						end
						local tmp = self.m_IntersectList[i]
						self.m_IntersectList[i] = self.m_IntersectList[j]
						self.m_IntersectList[j] = tmp
					end
					self:SwapPositionsInSEL(self.m_IntersectList[i].Edge1, self.m_IntersectList[i].Edge2)
				end
				return true
			end,

			ProcessIntersectList = function(self)
				for i = 1, #self.m_IntersectList do
					local iNode = self.m_IntersectList[i]
					self:IntersectEdges(iNode.Edge1, iNode.Edge2, iNode.Pt)
					self:SwapPositionsInAEL(iNode.Edge1, iNode.Edge2)
				end
				self.m_IntersectList = {}
			end,

			IntersectPoint = function(self, edge1, edge2, ip)
				ip.x = 0
				ip.y = 0
				local b1 = nil
				local b2 = nil
				if edge1.Dx == edge2.Dx then
					ip.y = edge1.Curr.y
					ip.x = ClipperLib.Clipper.TopX(edge1, ip.y)
					return
				end
				if edge1.Delta.x == 0 then
					ip.x = edge1.Bot.x
					if ClipperLib.ClipperBase.IsHorizontal(edge2) then
						ip.y = edge2.Bot.y
					else
						b2 = edge2.Bot.y - (edge2.Bot.x / edge2.Dx)
						ip.y = ip.x / edge2.Dx + b2
					end
				elseif edge2.Delta.x == 0 then
					ip.x = edge2.Bot.x
					if ClipperLib.ClipperBase.IsHorizontal(edge1) then
						ip.y = edge1.Bot.y
					else
						b1 = edge1.Bot.y - (edge1.Bot.x / edge1.Dx)
						ip.y = ip.x / edge1.Dx + b1
					end
				else
					b1 = edge1.Bot.x - edge1.Bot.y * edge1.Dx
					b2 = edge2.Bot.x - edge2.Bot.y * edge2.Dx
					local q = (b2 - b1) / (edge1.Dx - edge2.Dx)
					ip.y = q
					if math.abs(edge1.Dx) < math.abs(edge2.Dx) then
						ip.x = edge1.Dx * q + b1
					else
						ip.x = edge2.Dx * q + b2
					end
				end
				if ip.y < edge1.Top.y or ip.y < edge2.Top.y then
					if edge1.Top.y > edge2.Top.y then
						ip.y = edge1.Top.y
						ip.x = ClipperLib.Clipper.TopX(edge2, edge1.Top.y)
						return ip.x < edge1.Top.x
					else
						ip.y = edge2.Top.y
					end
					if math.abs(edge1.Dx) < math.abs(edge2.Dx) then
						ip.x = ClipperLib.Clipper.TopX(edge1, ip.y)
					else
						ip.x = ClipperLib.Clipper.TopX(edge2, ip.y)
					end
				end
				if ip.y > edge1.Curr.y then
					ip.y = edge1.Curr.y
					if math.abs(edge1.Dx) > math.abs(edge2.Dx) then
						ip.x = ClipperLib.Clipper.TopX(edge2, ip.y)
					else
						ip.x = ClipperLib.Clipper.TopX(edge1, ip.y)
					end
				end
			end,

			ProcessEdgesAtTopOfScanbeam = function(self, topY)
				local e = self.m_ActiveEdges
				while e ~= nil do
					local IsMaximaEdge = self:IsMaxima(e, topY)
					if IsMaximaEdge then
						local eMaxPair = self:GetMaximaPairEx(e)
						IsMaximaEdge = eMaxPair == nil or not ClipperLib.ClipperBase.IsHorizontal(eMaxPair)
					end
					if IsMaximaEdge then
						if self.StrictlySimple then
							self:InsertMaxima(e.Top.x)
						end
						local ePrev = e.PrevInAEL
						self:DoMaxima(e)
						if ePrev == nil then
							e = self.m_ActiveEdges
						else
							e = ePrev.NextInAEL
						end
					else
						if self:IsIntermediate(e, topY) and ClipperLib.ClipperBase.IsHorizontal(e.NextInLML) then
							e = self:UpdateEdgeIntoAEL(e)
							if e.OutIdx >= 0 then
								self:AddOutPt(e, e.Bot)
							end
							self:AddEdgeToSEL(e)
						else
							e.Curr.x = ClipperLib.Clipper.TopX(e, topY)
							e.Curr.y = topY
						end
						if self.StrictlySimple then
							local ePrev = e.PrevInAEL
							if ((e.OutIdx >= 0) and (e.WindDelta ~= 0) and ePrev ~= nil and (ePrev.OutIdx >= 0) and
								(ePrev.Curr.x == e.Curr.x) and (ePrev.WindDelta ~= 0)) then
								local ip = Point(e.Curr)
								local op = self:AddOutPt(ePrev, ip)
								local op2 = self:AddOutPt(e, ip)
								self:AddJoin(op, op2, ip)
							end
						end
						e = e.NextInAEL
					end
				end
				self:ProcessHorizontals()
				self.m_Maxima = nil
				e = self.m_ActiveEdges
				while e ~= nil do
					if self:IsIntermediate(e, topY) then
						local op = nil
						if e.OutIdx >= 0 then
							op = self:AddOutPt(e, e.Top)
						end
						e = self:UpdateEdgeIntoAEL(e)
						local ePrev = e.PrevInAEL
						local eNext = e.NextInAEL
						if (ePrev ~= nil and ePrev.Curr.x == e.Bot.x and ePrev.Curr.y == e.Bot.y and op ~= nil and
							ePrev.OutIdx >= 0 and ePrev.Curr.y == ePrev.Top.y and
							ClipperLib.ClipperBase.SlopesEqual(e.Curr, e.Top, ePrev.Curr, ePrev.Top) and (e.WindDelta ~= 0) and
							(ePrev.WindDelta ~= 0)) then
							local op2 = self:AddOutPt(ePrev2, e.Bot)
							self:AddJoin(op, op2, e.Top)
						elseif (eNext ~= nil and eNext.Curr.x == e.Bot.x and eNext.Curr.y == e.Bot.y and op ~= nil and
							eNext.OutIdx >= 0 and eNext.Curr.y == eNext.Top.y and
							ClipperLib.ClipperBase.SlopesEqual(e.Curr, e.Top, eNext.Curr, eNext.Top) and (e.WindDelta ~= 0) and
							(eNext.WindDelta ~= 0)) then
							local op2 = self:AddOutPt(eNext, e.Bot)
							self:AddJoin(op, op2, e.Top)
						end
					end
					e = e.NextInAEL
				end
			end,

			DoMaxima = function(self, e)
				local eMaxPair = self:GetMaximaPairEx(e)
				if eMaxPair == nil then
					if e.OutIdx >= 0 then
						self:AddOutPt(e, e.Top)
					end
					self:DeleteFromAEL(e)
					return
				end
				local eNext = e.NextInAEL
				while eNext ~= nil and eNext ~= eMaxPair do
					self:IntersectEdges(e, eNext, e.Top)
					self:SwapPositionsInAEL(e, eNext)
					eNext = e.NextInAEL
				end
				if e.OutIdx == -1 and eMaxPair.OutIdx == -1 then
					self:DeleteFromAEL(e)
					return self:DeleteFromAEL(eMaxPair)
				elseif e.OutIdx >= 0 and eMaxPair.OutIdx >= 0 then
					if e.OutIdx >= 0 then
						self:AddLocalMaxPoly(e, eMaxPair, e.Top)
					end
					self:DeleteFromAEL(e)
					return self:DeleteFromAEL(eMaxPair)
				elseif ClipperLib.use_lines and e.WindDelta == 0 then
					if e.OutIdx >= 0 then
						self:AddOutPt(e, e.Top)
						e.OutIdx = ClipperLib.ClipperBase.Unassigned
					end
					self:DeleteFromAEL(e)
					if eMaxPair.OutIdx >= 0 then
						self:AddOutPt(eMaxPair, e.Top)
						eMaxPair.OutIdx = ClipperLib.ClipperBase.Unassigned
					end
					return self:DeleteFromAEL(eMaxPair)
				else
					return ClipperLib.Error("DoMaxima error")
				end
			end,

			PointCount = function(self, pts)
				if pts == nil then
					return 0
				end
				local result = 0
				local p = pts
				while true do
					result = result + 1
					p = p.Next
					if p == pts then
						break
					end
				end
				return result
			end,

			BuildResult = function(self)
				local polyg = ClipperLib.Clear()
				for i = 1, #self.m_PolyOuts do
					local outRec = self.m_PolyOuts[i]
					if outRec.Pts == nil then
						goto continue
					end
					local p = outRec.Pts.Prev
					local cnt = self:PointCount(p)
					if cnt < 2 then
						goto continue
					end
					local pg = {cnt}
					for j = 1, cnt do
						pg[j] = p.Pt
						p = p.Prev
					end
					table.insert(polyg, pg)
					::continue::
				end
				self.FinalSolution = polyg
			end,

			FixupOutPolyline = function(self, outRec)
				local pp = outRec.Pts
				local lastPP = pp.Prev
				while pp ~= lastPP do
					pp = pp.Next
					if ClipperLib.Point.op_Equality(pp.Pt, pp.Prev.Pt) then
						if pp == lastPP then
							lastPP = pp.Prev
						end
						local tmpPP = pp.Prev
						tmpPP.Next = pp.Next
						pp.Next.Prev = tmpPP
						pp = tmpPP
					end
				end
				if pp == pp.Prev then
					outRec.Pts = nil
				end
			end,

			FixupOutPolygon = function(self, outRec)
				local lastOK = nil
				outRec.BottomPt = nil
				local pp = outRec.Pts
				local preserveCol = self.PreserveCollinear or self.StrictlySimple
				while true do
					if pp.Prev == pp or pp.Prev == pp.Next then
						outRec.Pts = nil
						return
					end
					if ((ClipperLib.Point.op_Equality(pp.Pt, pp.Next.Pt)) or
						(ClipperLib.Point.op_Equality(pp.Pt, pp.Prev.Pt)) or
						(ClipperLib.ClipperBase.SlopesEqual(pp.Prev.Pt, pp.Pt, pp.Next.Pt) and (not preserveCol or not self:Pt2IsBetweenPt1AndPt3(pp.Prev.Pt, pp.Pt, pp.Next.Pt)))) then
						lastOK = nil
						pp.Prev.Next = pp.Next
						pp.Next.Prev = pp.Prev
						pp = pp.Prev
					elseif pp == lastOK then
						break
					else
						if lastOK == nil then
							lastOK = pp
						end
						pp = pp.Next
					end
				end
				outRec.Pts = pp
			end,

			DupOutPt = function(self, outPt, InsertAfter)
				local result = OutPt()
				result.Pt.x = outPt.Pt.x
				result.Pt.y = outPt.Pt.y
				result.Idx = outPt.Idx
				if InsertAfter then
					result.Next = outPt.Next
					result.Prev = outPt
					outPt.Next.Prev = result
					outPt.Next = result
				else
					result.Prev = outPt.Prev
					result.Next = outPt
					outPt.Prev.Next = result
					outPt.Prev = result
				end
				return result
			end,

			GetOverlap = function(self, a1, a2, b1, b2, Sval)
				if a1 < a2 then
					if b1 < b2 then
						Sval.Left = math.max(a1, b1)
						Sval.Right = math.min(a2, b2)
					else
						Sval.Left = math.max(a1, b2)
						Sval.Right = math.min(a2, b1)
					end
				else
					if b1 < b2 then
						Sval.Left = math.max(a2, b1)
						Sval.Right = math.min(a1, b2)
					else
						Sval.Left = math.max(a2, b2)
						Sval.Right = math.min(a1, b1)
					end
				end
				return Sval.Left < Sval.Right
			end,

			JoinHorz = function(self, op1, op1b, op2, op2b, Pt, DiscardLeft)
				local Dir1 = nil
				local Dir2 = nil
				if op1.Pt.x > op1b.Pt.x then
					Dir1 = ClipperLib.Direction.dRightToLeft
				else
					Dir1 = ClipperLib.Direction.dLeftToRight
				end
				if op2.Pt.x > op2b.Pt.x then
					Dir2 = ClipperLib.Direction.dRightToLeft
				else
					Dir2 = ClipperLib.Direction.dLeftToRight
				end
				if Dir1 == Dir2 then
					return false
				end
				if Dir1 == ClipperLib.Direction.dLeftToRight then
					while op1.Next.Pt.x <= Pt.x and op1.Next.Pt.x >= op1.Pt.x and op1.Next.Pt.y == Pt.y do
						op1 = op1.Next
					end
					if DiscardLeft and op1.Pt.x ~= Pt.x then
						op1 = op1.Next
					end
					op1b = self:DupOutPt(op1, not DiscardLeft)
					if ClipperLib.Point.op_Inequality(op1b.Pt, Pt) then
						op1 = op1b
						op1.Pt.x = Pt.x
						op1.Pt.y = Pt.y
						op1b = self:DupOutPt(op1, not DiscardLeft)
					end
				else
					while op1.Next.Pt.x >= Pt.x and op1.Next.Pt.x <= op1.Pt.x and op1.Next.Pt.y == Pt.y do
						op1 = op1.Next
					end
					if not DiscardLeft and op1.Pt.x ~= Pt.x then
						op1 = op1.Next
					end
					op1b = self:DupOutPt(op1, DiscardLeft)
					if ClipperLib.Point.op_Inequality(op1b.Pt, Pt) then
						op1 = op1b
						op1.Pt.x = Pt.x
						op1.Pt.y = Pt.y
						op1b = self:DupOutPt(op1, DiscardLeft)
					end
				end
				if Dir2 == ClipperLib.Direction.dLeftToRight then
					while op2.Next.Pt.x <= Pt.x and op2.Next.Pt.x >= op2.Pt.x and op2.Next.Pt.y == Pt.y do
						op2 = op2.Next
					end
					if DiscardLeft and op2.Pt.x ~= Pt.x then
						op2 = op2.Next
					end
					op2b = self:DupOutPt(op2, not DiscardLeft)
					if ClipperLib.Point.op_Inequality(op2b.Pt, Pt) then
						op2 = op2b
						op2.Pt.x = Pt.x
						op2.Pt.y = Pt.y
						op2b = self:DupOutPt(op2, not DiscardLeft)
					end
				else
					while op2.Next.Pt.x >= Pt.x and op2.Next.Pt.x <= op2.Pt.x and op2.Next.Pt.y == Pt.y do
						op2 = op2.Next
					end
					if not DiscardLeft and op2.Pt.x ~= Pt.x then
						op2 = op2.Next
					end
					op2b = self:DupOutPt(op2, DiscardLeft)
					if ClipperLib.Point.op_Inequality(op2b.Pt, Pt) then
						op2 = op2b
						op2.Pt.x = Pt.x
						op2.Pt.y = Pt.y
						op2b = self:DupOutPt(op2, DiscardLeft)
					end
				end
				if (Dir1 == ClipperLib.Direction.dLeftToRight) == DiscardLeft then
					op1.Prev = op2
					op2.Next = op1
					op1b.Next = op2b
					op2b.Prev = op1b
				else
					op1.Next = op2
					op2.Prev = op1
					op1b.Prev = op2b
					op2b.Next = op1b
				end
				return true
			end,

			JoinPoints = function(self, j, outRec1, outRec2)
				local op1 = j.OutPt1
				local op1b = OutPt()
				local op2 = j.OutPt2
				local op2b = OutPt()
				local isHorizontal = j.OutPt1.Pt.y == j.OffPt.y
				if (isHorizontal and (ClipperLib.Point.op_Equality(j.OffPt, j.OutPt1.Pt)) and
					(ClipperLib.Point.op_Equality(j.OffPt, j.OutPt2.Pt))) then
					if outRec1 ~= outRec2 then
						return false
					end
					op1b = j.OutPt1.Next
					while op1b ~= op1 and ClipperLib.Point.op_Equality(op1b.Pt, j.OffPt) do
						op1b = op1b.Next
					end
					local reverse1 = op1b.Pt.y > j.OffPt.y
					op2b = j.OutPt2.Next
					while op2b ~= op2 and ClipperLib.Point.op_Equality(op2b.Pt, j.OffPt) do
						op2b = op2b.Next
					end
					local reverse2 = op2b.Pt.y > j.OffPt.y
					if reverse1 == reverse2 then
						return false
					end
					if reverse1 then
						op1b = self:DupOutPt(op1, false)
						op2b = self:DupOutPt(op2, true)
						op1.Prev = op2
						op2.Next = op1
						op1b.Next = op2b
						op2b.Prev = op1b
						j.OutPt1 = op1
						j.OutPt2 = op1b
						return true
					else
						op1b = self:DupOutPt(op1, true)
						op2b = self:DupOutPt(op2, false)
						op1.Next = op2
						op2.Prev = op1
						op1b.Prev = op2b
						op2b.Next = op1b
						j.OutPt1 = op1
						j.OutPt2 = op1b
						return true
					end
				elseif isHorizontal then
					op1b = op1
					while op1.Prev.Pt.y == op1.Pt.y and op1.Prev ~= op1b and op1.Prev ~= op2 do
						op1 = op1.Prev
					end
					while op1b.Next.Pt.y == op1b.Pt.y and op1b.Next ~= op1 and op1b.Next ~= op2 do
						op1b = op1b.Next
					end
					if op1b.Next == op1 or op1b.Next == op2 then
						return false
					end
					op2b = op2
					while op2.Prev.Pt.y == op2.Pt.y and op2.Prev ~= op2b and op2.Prev ~= op1b do
						op2 = op2.Prev
					end
					while op2b.Next.Pt.y == op2b.Pt.y and op2b.Next ~= op2 and op2b.Next ~= op1 do
						op2b = op2b.Next
					end
					if op2b.Next == op2 or op2b.Next == op1 then
						return false
					end
					local Sval = {Left = nil, Right = nil}
					if not self:GetOverlap(op1.Pt.x, op1b.Pt.x, op2.Pt.x, op2b.Pt.x, Sval) then
						return false
					end
					local Left = Sval.Left
					local Right = Sval.Right
					local Pt = Point()
					local DiscardLeftSide = nil
					if op1.Pt.x >= Left and op1.Pt.x <= Right then
						Pt.x = op1.Pt.x
						Pt.y = op1.Pt.y
						DiscardLeftSide = op1.Pt.x > op1b.Pt.x
					elseif op2.Pt.x >= Left and op2.Pt.x <= Right then
						Pt.x = op2.Pt.x
						Pt.y = op2.Pt.y
						DiscardLeftSide = op2.Pt.x > op2b.Pt.x
					elseif op1b.Pt.x >= Left and op1b.Pt.x <= Right then
						Pt.x = op1b.Pt.x
						Pt.y = op1b.Pt.y
						DiscardLeftSide = op1b.Pt.x > op1.Pt.x
					else
						Pt.x = op2b.Pt.x
						Pt.y = op2b.Pt.y
						DiscardLeftSide = (op2b.Pt.x > op2.Pt.x)
					end
					j.OutPt1 = op1
					j.OutPt2 = op2
					return self:JoinHorz(op1, op1b, op2, op2b, Pt, DiscardLeftSide)
				else
					op1b = op1.Next
					while ClipperLib.Point.op_Equality(op1b.Pt, op1.Pt) and op1b ~= op1 do
						op1b = op1b.Next
					end
					local Reverse1 = op1b.Pt.y > op1.Pt.y or not ClipperLib.ClipperBase.SlopesEqual(op1.Pt, op1b.Pt, j.OffPt)
					if Reverse1 then
						op1b = op1.Prev
						while ClipperLib.Point.op_Equality(op1b.Pt, op1.Pt) and op1b ~= op1 do
							op1b = op1b.Prev
						end
						if op1b.Pt.y > op1.Pt.y or not ClipperLib.ClipperBase.SlopesEqual(op1.Pt, op1b.Pt, j.OffPt) then
							return false
						end
					end
					op2b = op2.Next
					while ClipperLib.Point.op_Equality(op2b.Pt, op2.Pt) and op2b ~= op2 do
						op2b = op2b.Next
					end
					local Reverse2 = op2b.Pt.y > op2.Pt.y or not ClipperLib.ClipperBase.SlopesEqual(op2.Pt, op2b.Pt, j.OffPt)
					if Reverse2 then
						op2b = op2.Prev
						while ClipperLib.Point.op_Equality(op2b.Pt, op2.Pt) and op2b ~= op2 do
							op2b = op2b.Prev
						end
						if op2b.Pt.y > op2.Pt.y or not ClipperLib.ClipperBase.SlopesEqual(op2.Pt, op2b.Pt, j.OffPt) then
							return false
						end
					end
					if ((op1b == op1) or (op2b == op2) or (op1b == op2b) or ((outRec1 == outRec2) and (Reverse1 == Reverse2))) then
						return false
					end
					if Reverse1 then
						op1b = self:DupOutPt(op1, false)
						op2b = self:DupOutPt(op2, true)
						op1.Prev = op2
						op2.Next = op1
						op1b.Next = op2b
						op2b.Prev = op1b
						j.OutPt1 = op1
						j.OutPt2 = op1b
						return true
					else
						op1b = self:DupOutPt(op1, true)
						op2b = self:DupOutPt(op2, false)
						op1.Next = op2
						op2.Prev = op1
						op1b.Prev = op2b
						op2b.Next = op1b
						j.OutPt1 = op1
						j.OutPt2 = op1b
						return true
					end
				end
			end,

			GetBounds2 = function(self, ops)
				local opStart = ops
				local result = Rect()
				result.left = ops.Pt.x
				result.right = ops.Pt.x
				result.top = ops.Pt.y
				result.bottom = ops.Pt.y
				ops = ops.Next
				while ops ~= opStart do
					if ops.Pt.x < result.left then
						result.left = ops.Pt.x
					end
					if ops.Pt.x > result.right then
						result.right = ops.Pt.x
					end
					if ops.Pt.y < result.top then
						result.top = ops.Pt.y
					end
					if ops.Pt.y > result.bottom then
						result.bottom = ops.Pt.y
					end
					ops = ops.Next
				end
				return result
			end,

			PointInPolygon = function(self, pt, op)
				local result = 0
				local startOp = op
				local ptx = pt.x
				local pty = pt.y
				local poly0x = op.Pt.x
				local poly0y = op.Pt.y
				while true do
					op = op.Next
					local poly1x = op.Pt.x
					local poly1y = op.Pt.y
					if poly1y == pty then
						if ((poly1x == ptx) or (poly0y == pty and ((poly1x > ptx) == (poly0x < ptx)))) then
							return -1
						end
					end
					if poly0y < pty ~= poly1y < pty then
						if poly0x >= ptx then
							if poly1x > ptx then
								result = 1 - result
							else
								local d = (poly0x - ptx) * (poly1y - pty) - (poly1x - ptx) * (poly0y - pty)
								if d == 0 then
									return -1
								end
								if d > 0 == poly1y > poly0y then
									result = 1 - result
								end
							end
						else
							if poly1x > ptx then
								local d = (poly0x - ptx) * (poly1y - pty) - (poly1x - ptx) * (poly0y - pty)
								if d == 0 then
									return -1
								end
								if d > 0 == poly1y > poly0y then
									result = 1 - result
								end
							end
						end
					end
					poly0x = poly1x
					poly0y = poly1y
					if startOp == op then
						break
					end
				end
				return result
			end,

			Poly2ContainsPoly1 = function(self, outPt1, outPt2)
				local op = outPt1
				while true do
					local res = self:PointInPolygon(op.Pt, outPt2)
					if res >= 0 then
						return res > 0
					end
					op = op.Next
					if op == outPt1 then
						break
					end
				end
				return true
			end,

			JoinCommonEdges = function(self)
				for i = 1, #self.m_Joins do
					local join = self.m_Joins[i]
					local outRec1 = self:GetOutRec(join.OutPt1.Idx)
					local outRec2 = self:GetOutRec(join.OutPt2.Idx)
					if outRec1.Pts == nil or outRec2.Pts == nil then
						goto continue
					end
					if outRec1.IsOpen or outRec2.IsOpen then
						goto continue
					end
					local holeStateRec = nil
					if outRec1 == outRec2 then
						holeStateRec = outRec1
					elseif self:OutRec1RightOfOutRec2(outRec1, outRec2) then
						holeStateRec = outRec2
					elseif self:OutRec1RightOfOutRec2(outRec2, outRec1) then
						holeStateRec = outRec1
					else
						holeStateRec = self:GetLowermostRec(outRec1, outRec2)
					end
					if not self:JoinPoints(join, outRec1, outRec2) then
						goto continue
					end
					if outRec1 == outRec2 then
						outRec1.Pts = join.OutPt1
						outRec1.BottomPt = nil
						outRec2 = self:CreateOutRec()
						outRec2.Pts = join.OutPt2
						self:UpdateOutPtIdxs(outRec2)
						if self:Poly2ContainsPoly1(outRec2.Pts, outRec1.Pts) then
							outRec2.IsHole = not outRec1.IsHole
							outRec2.FirstLeft = outRec1
							if (BitXOR(outRec2.IsHole == true and 1 or 0, self.ReverseSolution == true and 1 or 0)) == ((self:AreaS1(outRec2) > 0) == true and 1 or 0) then
								self:ReversePolyPtLinks(outRec2.Pts)
							end
						elseif self:Poly2ContainsPoly1(outRec1.Pts, outRec2.Pts) then
							outRec2.IsHole = outRec1.IsHole
							outRec1.IsHole = not outRec2.IsHole
							outRec2.FirstLeft = outRec1.FirstLeft
							outRec1.FirstLeft = outRec2
							if (BitXOR(outRec1.IsHole == true and 1 or 0, self.ReverseSolution == true and 1 or 0)) == ((self:AreaS1(outRec1) > 0) == true and 1 or 0) then
								self:ReversePolyPtLinks(outRec1.Pts)
							end
						else
							outRec2.IsHole = outRec1.IsHole
							outRec2.FirstLeft = outRec1.FirstLeft
						end
					else
						outRec2.Pts = nil
						outRec2.BottomPt = nil
						outRec2.Idx = outRec1.Idx
						outRec1.IsHole = holeStateRec.IsHole
						if holeStateRec == outRec2 then
							outRec1.FirstLeft = outRec2.FirstLeft
						end
						outRec2.FirstLeft = outRec1
					end
					::continue::
				end
			end,

			UpdateOutPtIdxs = function(self, outrec)
				local op = outrec.Pts
				while true do
					op.Idx = outrec.Idx
					op = op.Prev
					if op == outrec.Pts then
						break
					end
				end
			end,

			DoSimplePolygons = function(self)
				local i = 1
				while i <= #self.m_PolyOuts do
					local outrec = self.m_PolyOuts[i]
					i = i + 1
					local op = outrec.Pts
					if op == nil or outrec.IsOpen then
						goto continue
					end
					while true do
						local op2 = op.Next
						while op2 ~= outrec.Pts do
							if ClipperLib.Point.op_Equality(op.Pt, op2.Pt) and op2.Next ~= op and op2.Prev ~= op then
								local op3 = op.Prev
								local op4 = op2.Prev
								op.Prev = op4
								op4.Next = op
								op2.Prev = op3
								op3.Next = op2
								outrec.Pts = op
								local outrec2 = self:CreateOutRec()
								outrec2.Pts = op2
								self:UpdateOutPtIdxs(outrec2)
								if self:Poly2ContainsPoly1(outrec2.Pts, outrec.Pts) then
									outrec2.IsHole = not outrec.IsHole
									outrec2.FirstLeft = outrec
								elseif self:Poly2ContainsPoly1(outrec.Pts, outrec2.Pts) then
									outrec2.IsHole = outrec.IsHole
									outrec.IsHole = not outrec2.IsHole
									outrec2.FirstLeft = outrec.FirstLeft
									outrec.FirstLeft = outrec2
								else
									outrec2.IsHole = outrec.IsHole
									outrec2.FirstLeft = outrec.FirstLeft
								end
								op2 = op
							end
							op2 = op2.Next
						end
						op = op.Next
						if op == outrec.Pts then
							break
						end
					end
					::continue::
				end
			end,

			Area = function(self, op)
				local opFirst = op
				if op == nil then
					return 0
				end
				local a = 0
				while true do
					a = a + (op.Prev.Pt.x + op.Pt.x) * (op.Prev.Pt.y - op.Pt.y)
					op = op.Next
					if op == opFirst then
						break
					end
				end
				return a * 0.5
			end,

			AreaS1 = function(self, outRec)
				return self:Area(outRec.Pts)
			end
		}
	)

	--CLASS CLIPPEROFFSET
	local ClipperOffset = class.create("ClipperOffset",
		function(self, miterLimit, arcTolerance)
			self.m_destPolys = Path()
			self.m_srcPoly = Path()
			self.m_destPoly = Path()
			self.m_normals = {}
			self.m_delta = 0
			self.m_sinA = 0
			self.m_sin = 0
			self.m_cos = 0
			self.m_miterLim = 0
			self.m_StepsPerRad = 0
			self.m_lowest = Point()
			self.m_polyNodes = PolyNode()
			self.MiterLimit = miterLimit or 2
			self.ArcTolerance = arcTolerance or ClipperLib.ClipperOffset.def_arc_tolerance
			self.m_lowest.x = -1
			self.FinalSolution = nil
		end,
		{
			Clear = function(self)
				ClipperLib.Clear()
				self.m_lowest.x = -1
			end,

			AddPath = function(self, path, joinType, endType)
				local highI = #path
				if highI < 1 then
					return
				end
				local newNode = PolyNode()
				newNode.m_jointype = joinType
				newNode.m_endtype = endType
				if endType == ClipperLib.EndType.etClosedLine or endType == ClipperLib.EndType.etClosedPolygon then
					while highI > 1 and ClipperLib.Point.op_Equality(path[1], path[highI]) do
						highI = highI - 1
					end
				end
				table.insert(newNode.m_polygon, path[1])
				local j = 1
				local k = 1
				for i = 2, highI do
					if ClipperLib.Point.op_Inequality(newNode.m_polygon[j], path[i]) then
						j = j + 1
						table.insert(newNode.m_polygon, path[i])
						if (path[i].y > newNode.m_polygon[k].y or
							(path[i].y == newNode.m_polygon[k].y and path[i].x < newNode.m_polygon[k].x)) then
							k = j
						end
					end
				end
				if endType == ClipperLib.EndType.etClosedPolygon and j < 3 then
					return
				end
				self.m_polyNodes:AddChild(newNode)
				if endType ~= ClipperLib.EndType.etClosedPolygon then
					return
				end
				if self.m_lowest.x < 0 then
					self.m_lowest = Point(self.m_polyNodes:ChildCount(), k)
				else
					local ip = self.m_polyNodes:Childs()[self.m_lowest.x].m_polygon[self.m_lowest.y]
					if (newNode.m_polygon[k].y > ip.y or (newNode.m_polygon[k].y == ip.y and newNode.m_polygon[k].x < ip.x)) then
						self.m_lowest = Point(self.m_polyNodes:ChildCount(), k)
					end
				end
			end,

			AddPaths = function(self, paths, joinType, endType)
				for i = 1, #paths do
					self:AddPath(paths[i], joinType, endType)
				end
			end,

			FixOrientations = function(self)
				if (self.m_lowest.x >= 0 and
					not ClipperLib.Clipper.Orientation(self.m_polyNodes:Childs()[self.m_lowest.x].m_polygon)) then
					for i = 1, self.m_polyNodes:ChildCount() do
						local node = self.m_polyNodes:Childs()[i]
						if (node.m_endtype == ClipperLib.EndType.etClosedPolygon or
							(node.m_endtype == ClipperLib.EndType.etClosedLine and
								ClipperLib.Clipper.Orientation(node.m_polygon))) then
							local tempNode = {}
							for i = #node.m_polygon, 1, -1 do
								table.insert(tempNode, node.m_polygon[i])
							end
							node.m_polygon = tempNode
						end
					end
				else
					for i = 1, self.m_polyNodes:ChildCount() do
						local node = self.m_polyNodes:Childs()[i]
						if (node.m_endtype == ClipperLib.EndType.etClosedLine and
							not ClipperLib.Clipper.Orientation(node.m_polygon)) then
							local tempNode = {}
							for i = #node.m_polygon, 1, -1 do
								table.insert(tempNode, node.m_polygon[i])
							end
							node.m_polygon = tempNode
						end
					end
				end
			end,

			DoOffset = function(self, delta)
				self.m_destPolys = {}
				self.m_delta = delta
				if ClipperLib.ClipperBase.near_zero(delta) then
				--if math.abs(delta) < 1E-10 then
					for i = 1, self.m_polyNodes:ChildCount() do
						local node = self.m_polyNodes:Childs()[i]
						if node.m_endtype == ClipperLib.EndType.etClosedPolygon then
							table.insert(self.m_destPolys, node.m_polygon)
						end
					end
					return
				end
				if self.MiterLimit > 2 then
					self.m_miterLim = 2 / (self.MiterLimit * self.MiterLimit)
				else
					self.m_miterLim = 0.5
				end
				local y = nil
				if self.ArcTolerance <= 0 then
					y = ClipperLib.ClipperOffset.def_arc_tolerance
				elseif self.ArcTolerance > math.abs(delta) * ClipperLib.ClipperOffset.def_arc_tolerance then
					y = math.abs(delta) * ClipperLib.ClipperOffset.def_arc_tolerance
				else
					y = self.ArcTolerance
				end
				local steps = 3.14159265358979 / math.acos(1 - y / math.abs(delta))
				self.m_sin = math.sin(ClipperLib.ClipperOffset.two_pi / steps)
				self.m_cos = math.cos(ClipperLib.ClipperOffset.two_pi / steps)
				self.m_StepsPerRad = steps / ClipperLib.ClipperOffset.two_pi
				if delta < 0 then
					self.m_sin = -self.m_sin
				end
				for i = 1, self.m_polyNodes:ChildCount() do
					local node = self.m_polyNodes:Childs()[i]
					self.m_srcPoly = node.m_polygon
					local len = #self.m_srcPoly
					if (len == 0 or (delta <= 0 and (len < 3 or node.m_endtype ~= ClipperLib.EndType.etClosedPolygon))) then
						goto continue
					end
					self.m_destPoly = {}
					if len == 1 then
						if node.m_jointype == ClipperLib.JoinType.jtRound then
							local X = 1
							local Y = 0
							for j = 1, steps do
								table.insert(self.m_destPoly, Point(self.m_srcPoly[1].x + X * delta, self.m_srcPoly[1].y + Y * delta))
								local X2 = X
								X = X * self.m_cos - self.m_sin * Y
								Y = X2 * self.m_sin + Y * self.m_cos
							end
						else
							local X = -1
							local Y = -1
							for j = 1, 4 do
								table.insert(self.m_destPoly, Point(self.m_srcPoly[1].x + X * delta, self.m_srcPoly[1].y + Y * delta))
								if X < 0 then
									X = 1
								elseif Y < 0 then
									Y = 1
								else
									X = -1
								end
							end
						end
						table.insert(self.m_destPolys, self.m_destPoly)
						goto continue
					end
					self.m_normals = {}
					for j = 1, len - 1 do
						table.insert(self.m_normals, ClipperLib.ClipperOffset.GetUnitNormal(self.m_srcPoly[j], self.m_srcPoly[j + 1]))
					end
					if (node.m_endtype == ClipperLib.EndType.etClosedLine or node.m_endtype == ClipperLib.EndType.etClosedPolygon) then
						table.insert(self.m_normals, ClipperLib.ClipperOffset.GetUnitNormal(self.m_srcPoly[len], self.m_srcPoly[1]))
					else
						table.insert(self.m_normals, Point(self.m_normals[len - 1]))
					end
					if node.m_endtype == ClipperLib.EndType.etClosedPolygon then
						local k = len
						for j = 1, len do
							k = self:OffsetPoint(j, k, node.m_jointype)
						end
						table.insert(self.m_destPolys, self.m_destPoly)
					elseif node.m_endtype == ClipperLib.EndType.etClosedLine then
						local k = len
						for j = 1, len do
							k = self:OffsetPoint(j, k, node.m_jointype)
						end
						table.insert(self.m_destPolys, self.m_destPoly)
						self.m_destPoly = {}
						local n = self.m_normals[len]
						for j = len, 2, -1 do
							self.m_normals[j] = Point(-self.m_normals[j - 1].x, -self.m_normals[j - 1].y)
						end
						self.m_normals[1] = Point(-n.x, -n.y)
						k = 1
						for j = len, 1, -1 do
							k = self:OffsetPoint(j, k, node.m_jointype)
						end
						table.insert(self.m_destPolys, self.m_destPoly)
					else
						local k = 1
						for j = 2, len - 1 do
							k = self:OffsetPoint(j, k, node.m_jointype)
						end
						local pt1 = nil
						if node.m_endtype == ClipperLib.EndType.etOpenButt then
							local j = len
							pt1 = Point(self.m_srcPoly[j].x + self.m_normals[j].x * delta, self.m_srcPoly[j].y + self.m_normals[j].y * delta)
							table.insert(self.m_destPoly, pt1)
							pt1 = Point(self.m_srcPoly[j].x - self.m_normals[j].x * delta, self.m_srcPoly[j].y - self.m_normals[j].y * delta)
							table.insert(self.m_destPoly, pt1)
						else
							local j = len
							k = len - 1
							self.m_sinA = 0
							self.m_normals[j] = Point(-self.m_normals[j].x, -self.m_normals[j].y)
							if node.m_endtype == ClipperLib.EndType.etOpenSquare then
								self:DoSquare(j, k)
							else
								self:DoRound(j, k)
							end
						end
						for j = len, 2, -1 do
							self.m_normals[j] = Point(-self.m_normals[j - 1].x, -self.m_normals[j - 1].y)
						end
						self.m_normals[1] = Point(-self.m_normals[2].x, -self.m_normals[2].y)
						k = len
						for j = k - 1, 2, -1 do
							k = self:OffsetPoint(j, k, node.m_jointype)
						end
						if node.m_endtype == ClipperLib.EndType.etOpenButt then
							pt1 = Point(self.m_srcPoly[1].x - self.m_normals[1].x * delta, self.m_srcPoly[1].y - self.m_normals[1].y * delta)
							table.insert(self.m_destPoly, pt1)
							pt1 = Point(self.m_srcPoly[1].x + self.m_normals[1].x * delta, self.m_srcPoly[1].y + self.m_normals[1].y * delta)
							table.insert(self.m_destPoly, pt1)
						else
							k = 1
							self.m_sinA = 0
							if node.m_endtype == ClipperLib.EndType.etOpenSquare then
								self:DoSquare(1, 2)
							else
								self:DoRound(1, 2)
							end
						end
						table.insert(self.m_destPolys, self.m_destPoly)
					end
					::continue::
				end
			end,

			Execute = function(self, delta)
				self:FixOrientations()
				self:DoOffset(delta)
				local clpr = Clipper()
				clpr:AddPaths(self.m_destPolys, ClipperLib.PolyType.ptSubject, true)
				if delta > 0 then
					clpr:Execute(ClipperLib.ClipType.ctUnion, ClipperLib.PolyFillType.pftPositive, ClipperLib.PolyFillType.pftPositive)
				else
					local r = ClipperLib.Clipper.GetBounds(self.m_destPolys)
					local outer = Path()
					table.insert(outer, Point(r.left - 10, r.bottom + 10))
					table.insert(outer, Point(r.right + 10, r.bottom + 10))
					table.insert(outer, Point(r.right + 10, r.top - 10))
					table.insert(outer, Point(r.left - 10, r.top - 10))
					clpr:AddPath(outer, ClipperLib.PolyType.ptSubject, true)
					clpr.ReverseSolution = true
					clpr:Execute(ClipperLib.ClipType.ctUnion, ClipperLib.PolyFillType.pftNegative, ClipperLib.PolyFillType.pftNegative)
					if #clpr.FinalSolution > 1 then
						table.remove(clpr.FinalSolution, 1)
					end
				end
				self.FinalSolution = clpr.FinalSolution
			end,

			OffsetPoint = function(self, j, k, jointype)
				self.m_sinA = (self.m_normals[k].x * self.m_normals[j].y) - (self.m_normals[j].x * self.m_normals[k].y)
				if self.m_sinA == 0 then
					return k
				elseif self.m_sinA > 1 then
					self.m_sinA = 1
				elseif self.m_sinA < -1 then
					self.m_sinA = -1
				end
				if self.m_sinA * self.m_delta < 0 then
					table.insert(self.m_destPoly, Point(self.m_srcPoly[j].x + self.m_normals[k].x * self.m_delta, self.m_srcPoly[j].y + self.m_normals[k].y * self.m_delta))
					table.insert(self.m_destPoly, Point(self.m_srcPoly[j]))
					table.insert(self.m_destPoly, Point(self.m_srcPoly[j].x + self.m_normals[j].x * self.m_delta, self.m_srcPoly[j].y + self.m_normals[j].y * self.m_delta))
				else
					if ClipperLib.JoinType.jtMiter == jointype then
						local r = 1 + (self.m_normals[j].x * self.m_normals[k].x + self.m_normals[j].y * self.m_normals[k].y)
						if r >= self.m_miterLim then
							self:DoMiter(j, k, r)
						else
							self:DoSquare(j, k)
						end
					elseif ClipperLib.JoinType.jtSquare == jointype then
						self:DoSquare(j, k)
					elseif ClipperLib.JoinType.jtRound == jointype then
						self:DoRound(j, k)
					end
				end
				k = j
				return k
			end,

			DoSquare = function(self, j, k)
				local dx = math.tan(math.atan2(self.m_sinA, self.m_normals[k].x * self.m_normals[j].x + self.m_normals[k].y * self.m_normals[j].y) / 4)
				table.insert(self.m_destPoly, Point(self.m_srcPoly[j].x + self.m_delta * (self.m_normals[k].x - self.m_normals[k].y * dx), self.m_srcPoly[j].y + self.m_delta * (self.m_normals[k].y + self.m_normals[k].x * dx)))
				return table.insert(self.m_destPoly, Point(self.m_srcPoly[j].x + self.m_delta * (self.m_normals[j].x + self.m_normals[j].y * dx), self.m_srcPoly[j].y + self.m_delta * (self.m_normals[j].y - self.m_normals[j].x * dx)))
			end,

			DoMiter = function(self, j, k, r)
				local q = self.m_delta / r
				return table.insert(self.m_destPoly, Point(self.m_srcPoly[j].x + (self.m_normals[k].x + self.m_normals[j].x) * q, self.m_srcPoly[j].y + (self.m_normals[k].y + self.m_normals[j].y) * q))
			end,

			DoRound = function(self, j, k)
				local a = math.atan2(self.m_sinA, self.m_normals[k].x * self.m_normals[j].x + self.m_normals[k].y * self.m_normals[j].y)
				local steps = math.max(self.m_StepsPerRad * math.abs(a), 1)
				local X = self.m_normals[k].x
				local Y = self.m_normals[k].y
				local X2 = nil
				for i = 1, steps + 1 do
					table.insert(self.m_destPoly, Point(self.m_srcPoly[j].x + X * self.m_delta, self.m_srcPoly[j].y + Y * self.m_delta))
					X2 = X
					X = X * self.m_cos - self.m_sin * Y
					Y = X2 * self.m_sin + Y * self.m_cos
				end
				return table.insert(self.m_destPoly, Point(self.m_srcPoly[j].x + self.m_normals[j].x * self.m_delta, self.m_srcPoly[j].y + self.m_normals[j].y * self.m_delta))
			end
		}
	)

	ClipperLib.ClipperBase.SlopesEqual = function(...)
		local a = {...}
		if #a == 2 then --ClipperLib.ClipperBase.SlopesEqual3 = (e1, e2) ->
			local e1, e2 = a[1], a[2]
			return ((e1.Delta.y) * (e2.Delta.x)) == ((e1.Delta.x) * (e2.Delta.y))
		elseif #a == 3 then --ClipperLib.ClipperBase.SlopesEqual4 = (pt1, pt2, pt3) ->
			local pt1, pt2, pt3 = a[1], a[2], a[3]
			return ((pt1.y - pt2.y) * (pt2.x - pt3.x)) - ((pt1.x - pt2.x) * (pt2.y - pt3.y)) == 0
		elseif #a == 4 then --ClipperLib.ClipperBase.SlopesEqual5 = (pt1, pt2, pt3, pt4) ->
			local pt1, pt2, pt3, pt4 = a[1], a[2], a[3], a[4]
			return ((pt1.y - pt2.y) * (pt3.x - pt4.x)) - ((pt1.x - pt2.x) * (pt3.y - pt4.y)) == 0
		end
	end

	ClipperLib.MyIntersectNodeSort.Compare = function(node1, node2)
		local i = node2.Pt.y - node1.Pt.y
		return i < 0
	end

	ClipperLib.Point.op_Equality = function(a, b)
		return a.x == b.x and a.y == b.y
	end

	ClipperLib.Point.op_Inequality = function(a, b)
		return a.x ~= b.x or a.y ~= b.y
	end

	ClipperLib.Error = function(msg)
		error(msg)
	end

	ClipperLib.ClipperBase.near_zero = function(val)
		return (val > -ClipperLib.ClipperBase.tolerance) and (val < ClipperLib.ClipperBase.tolerance)
	end

	ClipperLib.ClipperBase.IsHorizontal = function(e)
		return e.Delta.y == 0
	end

	ClipperLib.Clipper.SwapSides = function(edge1, edge2)
		local side = edge1.Side
		edge1.Side = edge2.Side
		edge2.Side = side
	end

	ClipperLib.Clipper.SwapPolyIndexes = function(edge1, edge2)
		local outIdx = edge1.OutIdx
		edge1.OutIdx = edge2.OutIdx
		edge2.OutIdx = outIdx
	end

	ClipperLib.Clipper.IntersectNodeSort = function(node1, node2)
		return node2.Pt.y - node1.Pt.y
	end

	ClipperLib.Clipper.TopX = function(edge, currentY)
		if currentY == edge.Top.y then
			return edge.Top.x
		end
		return edge.Bot.x + edge.Dx * (currentY - edge.Bot.y)
	end

	ClipperLib.Clipper.ReversePaths = function(polys)
		for i = 1, #polys do
			local reversed = {}
			for j = #polys[i], 1, -1 do
				table.insert(reversed, polys[i][j])
			end
			polys[i] = reversed
		end
	end

	ClipperLib.Clipper.Orientation = function(poly)
		return ClipperLib.Clipper.Area(poly) >= 0
	end

	ClipperLib.Clipper.GetBounds = function(paths)
		local i = 1
		local cnt = #paths
		while i < cnt and #paths[i] == 0 do
			i = i + 1
		end
		if i - 1 == cnt then
			return Rect(0, 0, 0, 0)
		end
		local result = Rect()
		result.left = paths[i][1].x
		result.right = result.left
		result.top = paths[i][1].y
		result.bottom = result.top
		for i = 1, cnt do
			for j = 1, #paths[i] do
				if paths[i][j].x < result.left then
					result.left = paths[i][j].x
				elseif paths[i][j].x > result.right then
					result.right = paths[i][j].x
				end
				if paths[i][j].y < result.top then
					result.top = paths[i][j].y
				elseif paths[i][j].y > result.bottom then
					result.bottom = paths[i][j].y
				end
			end
		end
		return result
	end

	ClipperLib.Clipper.PointInPolygon = function(pt, path)
		local result = 0
		local cnt = #path
		if cnt < 3 then
			return 0
		end
		local ip = path[1]
		for i = 1, cnt do
			local ipNext = nil
			if i == cnt then
				ipNext = path[1]
			else
				ipNext = path[i]
			end
			if ipNext.y == pt.y then
				if ((ipNext.x == pt.x) or (ip.y == pt.y and ((ipNext.x > pt.x) == (ip.x < pt.x)))) then
					return -1
				end
			end
			if ip.y < pt.y ~= ipNext.y < pt.y then
				if ip.x >= pt.x then
					if ipNext.x > pt.x then
						result = 1 - result
					else
						local d = (ip.x - pt.x) * (ipNext.y - pt.y) - (ipNext.x - pt.x) * (ip.y - pt.y)
						if d == 0 then
							return -1
						elseif d > 0 == ipNext.y > ip.y then
							result = 1 - result
						end
					end
				else
					if ipNext.x > pt.x then
						local d = (ip.x - pt.x) * (ipNext.y - pt.y) - (ipNext.x - pt.x) * (ip.y - pt.y)
						if d == 0 then
							return -1
						elseif d > 0 == ipNext.y > ip.y then
							result = 1 - result
						end
					end
				end
			end
			ip = ipNext
		end
		return result
	end

	ClipperLib.Clipper.ParseFirstLeft = function(FirstLeft)
		while FirstLeft ~= nil and FirstLeft.Pts == nil do
			FirstLeft = FirstLeft.FirstLeft
		end
		return FirstLeft
	end

	ClipperLib.Clipper.Area = function(poly)
		if not type(poly) ~= "table" then
			return 0
		end
		local cnt = #poly
		if cnt < 3 then
			return 0
		end
		local j
		local a = 0
		for i = 1, cnt - 1 do
			a = a + (poly[j].x + poly[i].x) * (poly[j].y - poly[i].y)
			j = i
		end
		return -a * 0.5
	end

	ClipperLib.Clipper.DistanceSqrd = function(pt1, pt2)
		local dx = pt1.x - pt2.x
		local dy = pt1.y - pt2.y
		return dx * dx + dy * dy
	end

	ClipperLib.Clipper.DistanceFromLineSqrd = function(pt, ln1, ln2)
		--The equation of a line in general form (Ax + By + C = 0)
		--given 2 points (x¹,y¹) & (x²,y²) is ...
		--(y¹ - y²)x + (x² - x¹)y + (y² - y¹)x¹ - (x² - x¹)y¹ = 0
		--A = (y¹ - y²); B = (x² - x¹); C = (y² - y¹)x¹ - (x² - x¹)y¹
		--perpendicular distance of point (x³,y³) = (Ax³ + By³ + C)/Sqrt(A² + B²)
		--see http://en.wikipedia.org/wiki/Perpendicular_distance
		local A = ln1.y - ln2.y
		local B = ln2.x - ln1.x
		local C = A * ln1.x + B * ln1.y
		C = A * pt.x + B * pt.y - C
		return (C * C) / (A * A + B * B)
	end

	ClipperLib.Clipper.SlopesNearCollinear = function(pt1, pt2, pt3, distSqrd)
		--this function is more accurate when the point that's GEOMETRICALLY
		--between the other 2 points is the one that's tested for distance.
		--nbwith 'spikes', either pt1 or pt3 is geometrically between the other pts
		if math.abs(pt1.x - pt2.x) > math.abs(pt1.y - pt2.y) then
			if pt1.x > pt2.x == pt1.x < pt3.x then
				return ClipperLib.Clipper.DistanceFromLineSqrd(pt1, pt2, pt3) < distSqrd
			elseif pt2.x > pt1.x == pt2.x < pt3.x then
				return ClipperLib.Clipper.DistanceFromLineSqrd(pt2, pt1, pt3) < distSqrd
			else
				return ClipperLib.Clipper.DistanceFromLineSqrd(pt3, pt1, pt2) < distSqrd
			end
		else
			if pt1.y > pt2.y == pt1.y < pt3.y then
				return ClipperLib.Clipper.DistanceFromLineSqrd(pt1, pt2, pt3) < distSqrd
			elseif pt2.y > pt1.y == pt2.y < pt3.y then
				return ClipperLib.Clipper.DistanceFromLineSqrd(pt2, pt1, pt3) < distSqrd
			else
				return ClipperLib.Clipper.DistanceFromLineSqrd(pt3, pt1, pt2) < distSqrd
			end
		end
	end

	ClipperLib.Clipper.PointsAreClose = function(pt1, pt2, distSqrd)
		local dx = pt1.x - pt2.x
		local dy = pt1.y - pt2.y
		return (dx * dx) + (dy * dy) <= distSqrd
	end

	ClipperLib.Clipper.ExcludeOp = function(op)
		local result = op.Prev
		result.Next = op.Next
		op.Next.Prev = result
		result.Idx = 0
		return result
	end

	ClipperLib.Clipper.CleanPolygon = function(path, distance)
		if distance == nil then
			distance = 1.415
		end
		--distance = proximity in units/pixels below which vertices will be stripped.
		--Default ~= sqrt(2) so when adjacent vertices or semi-adjacent vertices have
		--both x & y coords within 1 unit, then the second vertex will be stripped.
		local cnt = #path
		if cnt == 0 then
			return {}
		end
		local outPts = {cnt}
		for i = 1, cnt do
			outPts[i] = OutPt()
		end
		for i = 1, cnt do
			outPts[i].Pt = path[i]
			outPts[i].Next = outPts[(i + 1) % cnt]
			outPts[i].Next.Prev = outPts[i]
			outPts[i].Idx = 0
		end
		local distSqrd = distance * distance
		local op = outPts[0]
		while op.Idx == 0 and op.Next ~= op.Prev do
			if ClipperLib.Clipper.PointsAreClose(op.Pt, op.Prev.Pt, distSqrd) then
				op = ClipperLib.Clipper.ExcludeOp(op)
				cnt = cnt - 1
			elseif ClipperLib.Clipper.PointsAreClose(op.Prev.Pt, op.Next.Pt, distSqrd) then
				ClipperLib.Clipper.ExcludeOp(op.Next)
				op = ClipperLib.Clipper.ExcludeOp(op)
				cnt = cnt - 2
			elseif ClipperLib.Clipper.SlopesNearCollinear(op.Prev.Pt, op.Pt, op.Next.Pt, distSqrd) then
				op = ClipperLib.Clipper.ExcludeOp(op)
				cnt = cnt - 1
			else
				op.Idx = 1
				op = op.Next
			end
		end
		if cnt < 3 then
			cnt = 0
		end
		local result = {cnt}
		for i = 1, cnt do
			result[i] = Point(op.Pt)
			op = op.Next
		end
		outPts = nil
		return result
	end

	ClipperLib.Clipper.CleanPolygons = function(polys, distance)
		local result = {#polys}
		for i = 1, #polys do
			result[i] = ClipperLib.Clipper.CleanPolygon(polys[i], distance)
		end
		return result
	end

	ClipperLib.Clipper.SimplifyPolygons = function(polys)
		local c = Clipper()
		c.StrictlySimple = true
		c:AddPaths(polys, ClipperLib.PolyType.ptSubject, true)
		c:Execute(ClipperLib.ClipType.ctUnion, ClipperLib.PolyFillType.pftEvenOdd, ClipperLib.PolyFillType.pftEvenOdd)
		return c.FinalSolution
	end

	ClipperLib.ClipperOffset.GetUnitNormal = function(pt1, pt2)
		if pt2.x == pt1.x and pt2.y == pt1.y then
			return Point(0, 0)
		end
		local dx = (pt2.x - pt1.x)
		local dy = (pt2.y - pt1.y)
		local f = 1 / math.sqrt(dx * dx + dy * dy)
		dx = dx * f
		dy = dy * f
		return Point(dy, -dx)
	end

	return {
		ClipperLib = ClipperLib,
		Clipper = Clipper,
		ClipperOffset = ClipperOffset,
	}