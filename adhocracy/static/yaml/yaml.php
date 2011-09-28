<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>" />
<title><?php
	/*
	 * Print the <title> tag based on what is being viewed.
	 */
	global $page, $paged;

	wp_title( '|', true, 'right' );

	// Add the blog name.
	bloginfo( 'name' );

	// Add the blog description for the home/front page.
	$site_description = get_bloginfo( 'description', 'display' );
	if ( $site_description && ( is_home() || is_front_page() ) )
		echo " | $site_description";

	// Add a page number if necessary:
	if ( $paged >= 2 || $page >= 2 )
		echo ' | ' . sprintf( __( 'Page %s', 'twentyten' ), max( $paged, $page ) );

	?></title>
<link rel="profile" href="http://gmpg.org/xfn/11" />
<link rel="stylesheet" type="text/css" media="all" href="<?php bloginfo( 'stylesheet_url' ); ?>" />
<link rel="pingback" href="<?php bloginfo( 'pingback_url' ); ?>" />
<?php
	/* We add some JavaScript to pages with the comment form
	 * to support sites with threaded comments (when in use).
	 */
	if ( is_singular() && get_option( 'thread_comments' ) )
		wp_enqueue_script( 'comment-reply' );

	wp_head();
?>
  <!--[if lte IE 7]>
  <link href="css/patches/patch_my_layout.css" rel="stylesheet" type="text/css" />
  <![endif]-->
</head>

<body <?php body_class(); ?>>
   <!-- begin: header -->
  <header>
    <div id="header">
      <div class="page_margins">
        <div class="page">
          <div id="topnav">
            <!-- start: skip link navigation -->
            <a class="skip" title="skip link" href="#navigation">Skip to the navigation</a><span class="hideme">.</span>
            <a class="skip" title="skip link" href="#content">Skip to the content</a><span class="hideme">.</span>
            <!-- end: skip link navigation --><a href="#">Login</a> | <a href="#">Contact</a> | <a href="#">Imprint</a>
          </div>
          <a href="<?php echo home_url( '/' ); ?>" title="<?php echo esc_attr( get_bloginfo( 'name', 'display' ) ); ?>" rel="home"><?php bloginfo( 'name' ); ?></a>
          <div id="site-description"><?php bloginfo( 'description' ); ?></div>
        </div>
      </div>
    </div>
  </header>
  <!-- begin: navi -->
  <nav>
    <div class="page_margins">
      <div class="page">
        <div id="nav">
          <!-- skiplink anchor: navigation -->
          <a id="navigation" name="navigation"></a>
          <div class="hlist">
            <!-- main navigation: horizontal list -->
            <?php wp_nav_menu( array( 'container_class' => 'menu-header', 'theme_location' => 'primary' ) ); ?>
          </div>
        </div>
      </div>
    </div>
  </nav>
  <!-- begin: main content -->
  <div id="main">
    <div class="page_margins">
      <div class="page">
         <!-- begin: page content -->
        <section>
          <div id="col1">
            <div id="col1_content" class="clearfix">
              <!-- add your content here -->
            </div>
          </div>
        </section>
         <!-- begin: sidebar -->
        <aside>
          <div id="col3">
            <div id="col3_content" class="clearfix">
              <!-- add your content here -->
            </div>
            <!-- IE Column Clearing -->
            <div id="ie_clearing"> &#160; </div>
          </div>
        </aside>
      </div>
    </div>
  </div>
  <!-- begin: footer -->
  <footer>
    <div class="page_margins">
      <div class="page">
        <div id="footer">
          <?php	get_sidebar( 'footer' ); ?>
        </div>
      </div>
    </div>
  </footer>
  <?php wp_footer(); ?>
</body>
</html>