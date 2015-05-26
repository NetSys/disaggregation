/**
 * Constructs a new dot mark with default properties. Dots are not typically
 * constructed directly, but by adding to a panel or an existing mark via
 * {@link pv.Mark#add}.
 *
 * @class Represents a dot; a dot is simply a sized glyph centered at a given
 * point that can also be stroked and filled. The <tt>size</tt> property is
 * proportional to the area of the rendered glyph to encourage meaningful visual
 * encodings. Dots can visually encode up to eight dimensions of data, though
 * this may be unwise due to integrality. See {@link pv.Mark} for details on the
 * prioritization of redundant positioning properties.
 *
 * <p>See also the <a href="../../api/Dot.html">Dot guide</a>.
 *
 * @extends pv.Mark
 */
pv.Dot = function() {
  pv.Mark.call(this);
};

pv.Dot.prototype = pv.extend(pv.Mark)
    .property("size", Number)
    .property("radius", Number)
    .property("shape", String)
    .property("angle", Number)
    .property("lineWidth", Number)
    .property("strokeStyle", pv.color)
    .property("fillStyle", pv.color);

pv.Dot.prototype.type = "dot";

/**
 * The size of the dot, in square pixels. Square pixels are used such that the
 * area of the dot is linearly proportional to the value of the size property,
 * facilitating representative encodings.
 *
 * @see #radius
 * @type number
 * @name pv.Dot.prototype.size
 */

/**
 * The radius of the dot, in pixels. This is an alternative to using
 * {@link #size}.
 *
 * @see #size
 * @type number
 * @name pv.Dot.prototype.radius
 */

/**
 * The shape name. Several shapes are supported:<ul>
 *
 * <li>cross
 * <li>triangle
 * <li>diamond
 * <li>square
 * <li>circle
 * <li>tick
 * <li>bar
 *
 * </ul>These shapes can be further changed using the {@link #angle} property;
 * for instance, a cross can be turned into a plus by rotating. Similarly, the
 * tick, which is vertical by default, can be rotated horizontally. Note that
 * some shapes (cross and tick) do not have interior areas, and thus do not
 * support fill style meaningfully.
 *
 * <p>Note: it may be more natural to use the {@link pv.Rule} mark for
 * horizontal and vertical ticks. The tick shape is only necessary if angled
 * ticks are needed.
 *
 * @type string
 * @name pv.Dot.prototype.shape
 */

/**
 * The rotation angle, in radians. Used to rotate shapes, such as to turn a
 * cross into a plus.
 *
 * @type number
 * @name pv.Dot.prototype.angle
 */

/**
 * The width of stroked lines, in pixels; used in conjunction with
 * <tt>strokeStyle</tt> to stroke the dot's shape.
 *
 * @type number
 * @name pv.Dot.prototype.lineWidth
 */

/**
 * The style of stroked lines; used in conjunction with <tt>lineWidth</tt> to
 * stroke the dot's shape. The default value of this property is a categorical
 * color.
 *
 * @type string
 * @name pv.Dot.prototype.strokeStyle
 * @see pv.color
 */

/**
 * The fill style; if non-null, the interior of the dot is filled with the
 * specified color. The default value of this property is null, meaning dots are
 * not filled by default.
 *
 * @type string
 * @name pv.Dot.prototype.fillStyle
 * @see pv.color
 */

/**
 * Default properties for dots. By default, there is no fill and the stroke
 * style is a categorical color. The default shape is "circle" with size 20.
 *
 * @type pv.Dot
 */
pv.Dot.prototype.defaults = new pv.Dot()
    .extend(pv.Mark.prototype.defaults)
    .size(20)
    .shape("circle")
    .lineWidth(1.5)
    .strokeStyle(pv.Colors.category10().by(pv.parent));

/**
 * Constructs a new dot anchor with default properties. Dots support five
 * different anchors:<ul>
 *
 * <li>top
 * <li>left
 * <li>center
 * <li>bottom
 * <li>right
 *
 * </ul>In addition to positioning properties (left, right, top bottom), the
 * anchors support text rendering properties (text-align, text-baseline). Text is
 * rendered to appear outside the dot. Note that this behavior is different from
 * other mark anchors, which default to rendering text <i>inside</i> the mark.
 *
 * <p>For consistency with the other mark types, the anchor positions are
 * defined in terms of their opposite edge. For example, the top anchor defines
 * the bottom property, such that a bar added to the top anchor grows upward.
 *
 * @param {string} name the anchor name; either a string or a property function.
 * @returns {pv.Anchor}
 */
pv.Dot.prototype.anchor = function(name) {
  return pv.Mark.prototype.anchor.call(this, name)
    .left(function() {
        var s = this.scene.target[this.index];
        switch (this.name()) {
          case "bottom":
          case "top":
          case "center": return s.left;
          case "left": return null;
        }
        return s.left + s.radius;
      })
    .right(function() {
        var s = this.scene.target[this.index];
        return this.name() == "left" ? s.right + s.radius : null;
      })
    .top(function() {
        var s = this.scene.target[this.index];
        switch (this.name()) {
          case "left":
          case "right":
          case "center": return s.top;
          case "top": return null;
        }
        return s.top + s.radius;
      })
    .bottom(function() {
        var s = this.scene.target[this.index];
        return this.name() == "top" ? s.bottom + s.radius : null;
      })
    .textAlign(function() {
        switch (this.name()) {
          case "left": return "right";
          case "bottom":
          case "top":
          case "center": return "center";
        }
        return "left";
      })
    .textBaseline(function() {
        switch (this.name()) {
          case "right":
          case "left":
          case "center": return "middle";
          case "bottom": return "top";
        }
        return "bottom";
      });
};

/** @private Sets radius based on size or vice versa. */
pv.Dot.prototype.buildImplied = function(s) {
  if (s.radius == null) s.radius = Math.sqrt(s.size);
  else if (s.size == null) s.size = s.radius * s.radius;
  pv.Mark.prototype.buildImplied.call(this, s);
};
